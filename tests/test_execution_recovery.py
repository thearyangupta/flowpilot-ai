from sqlalchemy.orm import Session

from app.services.workflow_runner import resume
from app.models.enums import (
    ExecutionStatus,
    StepRunStatus,
)
from app.models.step_run import StepRun
from app.models.workflow import Workflow
from app.services.execution.execution_service import (
    create_or_return_existing,
    get_execution_events,
)
from tests.recovery_handlers import RecordingHandler

def test_crash_and_resume_recovers_from_checkpoint(
    db_session: Session,
    workflow: Workflow,
):
    execution, created = create_or_return_existing(
        db=db_session,
        workflow_id=workflow.id,
        idempotency_key="crash-resume-001",
        initial_context={
            "request_id": "request-123",
        },
    )

    assert created is True

    execution.status = ExecutionStatus.RUNNING

    first_step = workflow.steps[0]
    second_step = workflow.steps[1]

    completed_step_run = StepRun(
        execution_id=execution.id,
        workflow_step_id=first_step.id,
        status=StepRunStatus.COMPLETED,
        input_data={
            "request_id": "request-123",
        },
        output_data={
            "request_id": "request-123",
            "step1": "completed-before-crash",
        },
        attempt_count=1,
    )

    db_session.add(completed_step_run)
    db_session.add(execution)
    db_session.commit()

    db_session.refresh(execution)

    first_handler = RecordingHandler(
        value="should-not-run",
    )

    second_handler = RecordingHandler(
        value="completed-after-resume",
    )

    step_registry = {
        "step1": first_handler,
        "step2": second_handler,
    }

    resumed_execution = resume(
        db=db_session,
        execution=execution,
        step_registry=step_registry,
    )

    assert first_handler.calls == 0
    assert second_handler.calls == 1
    assert resumed_execution.status == ExecutionStatus.COMPLETED

    events = get_execution_events(
        db=db_session,
        execution_id=resumed_execution.id,
    )

    event_types = [
        event.event_type
        for event in events
    ]

    assert event_types == [
        "execution.resumed",
        "step.started",
        "step.completed",
        "execution.completed",
    ]

    resumed_event = events[0]

    assert resumed_event.details["resumed_step_id"] == str(
        second_step.id
    )
    assert resumed_event.details["resumed_position"] == 2

    assert events[1].details["resumed"] is True
    assert events[2].details["resumed"] is True
    assert events[3].details["resumed"] is True