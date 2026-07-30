from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ExecutionStatus, StepRunStatus
from app.models.execution import Execution
from app.models.project import Project
from app.models.step_run import StepRun
from app.models.workflow import Workflow
from app.models.workflow_step import WorkflowStep
from app.schemas.execution import ExecutionCreate
from app.services.project_service import create_execution


def test_create_execution_runs_workflow_successfully(
    db_session: Session,
) -> None:
    # Arrange
    project = Project(
        name="Test Project",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    workflow = Workflow(
        project_id=project.id,
        name="Test Workflow",
    )
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)

    step = WorkflowStep(
        workflow_id=workflow.id,
        position=1,
        step_type="set_value",
        config={
            "key": "message",
            "value": "Hello",
        },
    )
    db_session.add(step)
    db_session.commit()
    db_session.refresh(step)

    # Act
    execution,created = create_execution(
        db=db_session,
        project_id=project.id,
        workflow_id=workflow.id,
        payload=ExecutionCreate(
            idempotency_key="test-execution-001",
            input_data={},
        ),
    )

    # Assert
    assert created is True
    assert execution.status == ExecutionStatus.COMPLETED
    assert execution.workflow_id == workflow.id

    saved_execution = db_session.get(
        Execution,
        execution.id,
    )

    assert saved_execution is not None
    assert saved_execution.status == ExecutionStatus.COMPLETED

    step_runs = db_session.scalars(
        select(StepRun).where(
            StepRun.execution_id == execution.id
        )
    ).all()

    assert len(step_runs) == 1

    step_run = step_runs[0]

    assert step_run.status == StepRunStatus.COMPLETED
    assert step_run.input_data == {}
    assert step_run.output_data == {
        "message": "Hello",
    }