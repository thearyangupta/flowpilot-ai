from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmptyWorkflowError,
    InvalidStepOrder,
    UnsupportedStepType,
)
from app.domain.step_registry import is_step_registered
from app.models.project import Project
from app.models.workflow import Workflow
from app.models.workflow_step import WorkflowStep
from app.schemas.workflow import (
    StepCreate,
    WorkflowCreate,
)


def validate_steps(
    steps: list[StepCreate],
) -> None:
    if not steps:
        raise EmptyWorkflowError()

    positions = [
        step.position
        for step in steps
    ]

    expected_positions = list(
        range(
            1,
            len(steps) + 1,
        )
    )

    if sorted(positions) != expected_positions:
        raise InvalidStepOrder(
            positions
        )

    unsupported_step_types = sorted(
        {
            step.step_type
            for step in steps
            if not is_step_registered(
                step.step_type
            )
        }
    )

    if unsupported_step_types:
        raise UnsupportedStepType(
            unsupported_step_types
        )


def create_workflow_definition(
    db: Session,
    project_id: UUID,
    user_id: UUID,
    payload: WorkflowCreate,
) -> Workflow:
    validate_steps(
        payload.steps
    )

    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user_id,
        )
    )

    if project is None:
        raise ValueError(
            "Project not found"
        )

    existing_workflow = db.scalar(
        select(Workflow).where(
            Workflow.project_id == project.id,
            Workflow.name == payload.name,
        )
    )

    if existing_workflow is not None:
        return existing_workflow

    try:
        workflow = Workflow(
            project_id=project.id,
            name=payload.name,
        )

        db.add(workflow)
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

        db.add_all(
            workflow_steps
        )

        db.commit()
        db.refresh(workflow)

        return workflow

    except Exception:
        db.rollback()
        raise
