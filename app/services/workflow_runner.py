from sqlalchemy.orm import Session

from app.domain.execution_state import ensure_transition
from app.models.enums import ExecutionStatus, StepRunStatus
from app.models.execution import Execution
from app.models.step_run import StepRun
from app.domain.step_registry import (
    StepHandler,
    get_step_handler,
)


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

    db.add(execution)
    db.commit()
    db.refresh(execution)

    context = initial_context.copy()

    try:
        for step in execution.workflow.steps:
            step_run = StepRun(
                execution_id=execution.id,
                workflow_step_id=step.id,
                status=StepRunStatus.RUNNING,
                input_data=context.copy(),
            )

            db.add(step_run)
            db.commit()
            db.refresh(step_run)

            try:
                handler = get_step_handler(step.step_type,step_registry)

                context = handler(
                    context,
                    step.config,
                )

                step_run.output_data = context.copy()
                step_run.status = StepRunStatus.COMPLETED

                db.add(step_run)
                db.commit()
                db.refresh(step_run)

            except Exception as exc:
                step_run.status = StepRunStatus.FAILED
                step_run.error = str(exc)

                db.add(step_run)
                db.commit()
                db.refresh(step_run)

                raise

        ensure_transition(
            current=execution.status,
            target=ExecutionStatus.COMPLETED,
        )

        execution.status = ExecutionStatus.COMPLETED

        db.add(execution)
        db.commit()
        db.refresh(execution)

    except Exception:
        db.rollback()
        ensure_transition(
            current=execution.status,
            target=ExecutionStatus.FAILED,
        )

        execution.status = ExecutionStatus.FAILED

        db.add(execution)
        db.commit()
        db.refresh(execution)

        raise

    return execution