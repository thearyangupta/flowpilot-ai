from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.execution_state import ensure_transition
from app.domain.retry import RetryPolicy, execute_with_retry
from app.domain.step_registry import (
    StepHandler,
    get_step_handler,
)
from app.models.enums import ExecutionStatus, StepRunStatus
from app.models.execution import Execution
from app.models.step_run import StepRun
from app.services.execution_event_service import create_execution_event


def _get_completed_checkpoints(
    execution: Execution,
) -> dict:
    return {
        step_run.workflow_step_id: step_run
        for step_run in execution.step_runs
        if step_run.status == StepRunStatus.COMPLETED
    }


def run(
    db: Session,
    execution: Execution,
    initial_context: dict,
    step_registry: dict[str, StepHandler] | None = None,
) -> Execution:
    ensure_transition(
        current=execution.status,
        target=ExecutionStatus.RUNNING,
    )

    execution.status = ExecutionStatus.RUNNING

    create_execution_event(
        db=db,
        execution_id=execution.id,
        event_type="execution.started",
        details={
            "workflow_id": str(execution.workflow_id),
        },
        actor="workflow_runner",
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    context = initial_context.copy()

    try:
        for step in execution.workflow.steps:
            step_run = StepRun(
                execution_id=execution.id,
                workflow_step_id=step.id,
                status=StepRunStatus.PENDING,
                input_data=context.copy(),
            )

            db.add(step_run)
            db.commit()
            db.refresh(step_run)

            try:
                step_run.status = StepRunStatus.RUNNING
                step_run.started_at = datetime.now(timezone.utc)

                db.add(step_run)
                db.commit()
                db.refresh(step_run)

                handler = get_step_handler(
                    step.step_type,
                    step_registry,
                )

                def run_step_attempt() -> dict:
                    step_run.attempt_count += 1

                    create_execution_event(
                        db=db,
                        execution_id=execution.id,
                        event_type="step.started",
                        details={
                            "step_id": str(step.id),
                            "step_run_id": str(step_run.id),
                            "step_type": step.step_type,
                            "attempt": step_run.attempt_count,
                        },
                        actor="workflow_runner",
                    )

                    db.add(step_run)
                    db.commit()
                    db.refresh(step_run)

                    return handler(
                        context,
                        step.config,
                    )

                context = execute_with_retry(
                    operation=run_step_attempt,
                    policy=RetryPolicy(),
                )

                step_run.output_data = context.copy()
                step_run.status = StepRunStatus.COMPLETED
                step_run.finished_at = datetime.now(timezone.utc)

                create_execution_event(
                    db=db,
                    execution_id=execution.id,
                    event_type="step.completed",
                    details={
                        "step_id": str(step.id),
                        "step_run_id": str(step_run.id),
                        "step_type": step.step_type,
                        "attempt": step_run.attempt_count,
                    },
                    actor="workflow_runner",
                )

                db.add(step_run)
                db.commit()
                db.refresh(step_run)

            except Exception as exc:
                step_run.status = StepRunStatus.FAILED
                step_run.finished_at = datetime.now(timezone.utc)
                step_run.error_type = type(exc).__name__
                step_run.error_message = str(exc)

                create_execution_event(
                    db=db,
                    execution_id=execution.id,
                    event_type="step.failed",
                    details={
                        "step_id": str(step.id),
                        "step_run_id": str(step_run.id),
                        "step_type": step.step_type,
                        "attempt": step_run.attempt_count,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    },
                    actor="workflow_runner",
                )

                db.add(step_run)
                db.commit()
                db.refresh(step_run)

                raise

        ensure_transition(
            current=execution.status,
            target=ExecutionStatus.COMPLETED,
        )

        execution.status = ExecutionStatus.COMPLETED

        create_execution_event(
            db=db,
            execution_id=execution.id,
            event_type="execution.completed",
            details={
                "workflow_id": str(execution.workflow_id),
            },
            actor="workflow_runner",
        )

        db.add(execution)
        db.commit()
        db.refresh(execution)

    except Exception as exc:
        db.rollback()

        ensure_transition(
            current=execution.status,
            target=ExecutionStatus.FAILED,
        )

        execution.status = ExecutionStatus.FAILED

        create_execution_event(
            db=db,
            execution_id=execution.id,
            event_type="execution.failed",
            details={
                "workflow_id": str(execution.workflow_id),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            actor="workflow_runner",
        )

        db.add(execution)
        db.commit()
        db.refresh(execution)

        raise

    return execution


def resume(
    db: Session,
    execution: Execution,
    step_registry: dict[str, StepHandler] | None = None,
) -> Execution:
    completed_checkpoints = _get_completed_checkpoints(execution)

    context = dict(execution.input_data or {})

    workflow_steps = list(execution.workflow.steps)

    first_incomplete_step = None

    for step in workflow_steps:
        checkpoint = completed_checkpoints.get(step.id)

        if checkpoint:
            context = dict(checkpoint.output_data or {})
            continue

        first_incomplete_step = step
        break

    # Every workflow step already has a completed checkpoint.
    if first_incomplete_step is None:
        if execution.status == ExecutionStatus.COMPLETED:
            return execution

        execution.status = ExecutionStatus.COMPLETED

        create_execution_event(
            db=db,
            execution_id=execution.id,
            event_type="execution.completed",
            details={
                "workflow_id": str(execution.workflow_id),
                "recovered_from_checkpoints": True,
            },
            actor="workflow_runner",
        )

        db.add(execution)
        db.commit()
        db.refresh(execution)

        return execution

    resume_index = workflow_steps.index(first_incomplete_step)
    remaining_steps = workflow_steps[resume_index:]

    execution.status = ExecutionStatus.RUNNING

    create_execution_event(
        db=db,
        execution_id=execution.id,
        event_type="execution.resumed",
        details={
            "workflow_id": str(execution.workflow_id),
            "resumed_step_id": str(first_incomplete_step.id),
            "resumed_position": first_incomplete_step.position,
        },
        actor="workflow_runner",
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    try:
        for step in remaining_steps:
            step_run = StepRun(
                execution_id=execution.id,
                workflow_step_id=step.id,
                status=StepRunStatus.PENDING,
                input_data=context.copy(),
            )

            db.add(step_run)
            db.commit()
            db.refresh(step_run)

            try:
                step_run.status = StepRunStatus.RUNNING
                step_run.started_at = datetime.now(timezone.utc)

                db.add(step_run)
                db.commit()
                db.refresh(step_run)

                handler = get_step_handler(
                    step.step_type,
                    step_registry,
                )

                def run_step_attempt() -> dict:
                    step_run.attempt_count += 1

                    create_execution_event(
                        db=db,
                        execution_id=execution.id,
                        event_type="step.started",
                        details={
                            "step_id": str(step.id),
                            "step_run_id": str(step_run.id),
                            "step_type": step.step_type,
                            "attempt": step_run.attempt_count,
                            "resumed": True,
                        },
                        actor="workflow_runner",
                    )

                    db.add(step_run)
                    db.commit()
                    db.refresh(step_run)

                    return handler(
                        context,
                        step.config,
                    )

                context = execute_with_retry(
                    operation=run_step_attempt,
                    policy=RetryPolicy(),
                )

                step_run.output_data = context.copy()
                step_run.status = StepRunStatus.COMPLETED
                step_run.finished_at = datetime.now(timezone.utc)

                create_execution_event(
                    db=db,
                    execution_id=execution.id,
                    event_type="step.completed",
                    details={
                        "step_id": str(step.id),
                        "step_run_id": str(step_run.id),
                        "step_type": step.step_type,
                        "attempt": step_run.attempt_count,
                        "resumed": True,
                    },
                    actor="workflow_runner",
                )

                db.add(step_run)
                db.commit()
                db.refresh(step_run)

            except Exception as exc:
                step_run.status = StepRunStatus.FAILED
                step_run.finished_at = datetime.now(timezone.utc)
                step_run.error_type = type(exc).__name__
                step_run.error_message = str(exc)

                create_execution_event(
                    db=db,
                    execution_id=execution.id,
                    event_type="step.failed",
                    details={
                        "step_id": str(step.id),
                        "step_run_id": str(step_run.id),
                        "step_type": step.step_type,
                        "attempt": step_run.attempt_count,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                        "resumed": True,
                    },
                    actor="workflow_runner",
                )

                db.add(step_run)
                db.commit()
                db.refresh(step_run)

                raise

        execution.status = ExecutionStatus.COMPLETED

        create_execution_event(
            db=db,
            execution_id=execution.id,
            event_type="execution.completed",
            details={
                "workflow_id": str(execution.workflow_id),
                "resumed": True,
            },
            actor="workflow_runner",
        )

        db.add(execution)
        db.commit()
        db.refresh(execution)

    except Exception as exc:
        db.rollback()

        execution.status = ExecutionStatus.FAILED

        create_execution_event(
            db=db,
            execution_id=execution.id,
            event_type="execution.failed",
            details={
                "workflow_id": str(execution.workflow_id),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "resumed": True,
            },
            actor="workflow_runner",
        )

        db.add(execution)
        db.commit()
        db.refresh(execution)

        raise

    return execution