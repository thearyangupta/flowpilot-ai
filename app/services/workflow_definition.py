from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmptyWorkflowError,
    InvalidStepOrder,
    UnsupportedStepType,
)
from app.models.workflow import Workflow
from app.models.workflow_step import WorkflowStep
from app.schemas.workflow import StepCreate, WorkflowCreate
from app.models.project import Project

SUPPORTED_STEPS = {
    "set_value",
    "uppercase",
    "require_key",
}


def validate_steps(steps: list[StepCreate]) -> None:
    if not steps:
        raise EmptyWorkflowError()

    positions = [step.position for step in steps]
    expected = list(range(1, len(steps) + 1))

    if sorted(positions) != expected:
        raise InvalidStepOrder(positions)

    unknown = sorted(
        {
            step.step_type
            for step in steps
            if step.step_type not in SUPPORTED_STEPS
        }
    )

    if unknown:
        raise UnsupportedStepType(unknown)


def create_workflow_definition(
    db: Session,
    project_id: UUID,
    payload: WorkflowCreate,
) -> Workflow:
    validate_steps(payload.steps)
    project = db.get(Project, project_id)

    if project is None:
        raise ValueError("Project not found")
    try:
        workflow = Workflow(
            project_id=project_id,
            name=payload.name,
        )

        db.add(workflow)

        # Makes workflow.id available without committing the transaction.
        db.flush()

        ordered_steps = sorted(
            payload.steps,
            key=lambda step: step.position,
        )

        workflow_steps = [
            WorkflowStep(
                workflow_id=workflow.id,
                position=step.position,
                step_type=step.step_type,
                config=step.config.model_dump(),
            )
            for step in ordered_steps
        ]

        db.add_all(workflow_steps)
        db.commit()
        db.refresh(workflow)

        return workflow

    except Exception:
        db.rollback()
        raise