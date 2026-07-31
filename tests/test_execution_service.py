from sqlalchemy.orm import Session

from app.models.enums import ExecutionStatus
from app.models.execution import Execution
from app.models.project import Project
from app.models.workflow import Workflow
from app.models.workflow_step import WorkflowStep
from app.schemas.execution import ExecutionCreate
from app.services.project_service import create_execution


def test_create_execution_queues_workflow_successfully(
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
    execution, created = create_execution(
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
    assert execution.status == ExecutionStatus.QUEUED
    assert execution.workflow_id == workflow.id
    assert execution.idempotency_key == "test-execution-001"
    assert execution.input_data == {}

    saved_execution = db_session.get(
        Execution,
        execution.id,
    )

    assert saved_execution is not None
    assert saved_execution.status == ExecutionStatus.QUEUED
    assert saved_execution.workflow_id == workflow.id
    assert saved_execution.idempotency_key == "test-execution-001"
    assert saved_execution.input_data == {}