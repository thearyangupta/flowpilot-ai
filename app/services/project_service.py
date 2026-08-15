from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ExecutionStatus
from app.models.execution import Execution
from app.models.project import Project
from app.models.workflow import Workflow
from app.schemas.execution import ExecutionCreate
from app.schemas.project import ProjectCreate
from app.services.execution.execution_service import (
    create_or_return_existing,
)


def create(
    db: Session,
    payload: ProjectCreate,
    user_id: UUID,
) -> Project:
    project = Project(
        user_id=user_id,
        **payload.model_dump(),
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


def get_all(
    db: Session,
    user_id: UUID,
) -> list[Project]:
    statement = (
        select(Project)
        .where(
            Project.user_id == user_id
        )
        .order_by(
            Project.created_at.desc()
        )
    )

    projects = db.scalars(statement).all()

    return list(projects)


def require_owned_project(
    db: Session,
    project_id: UUID,
    user_id: UUID,
) -> Project:
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user_id,
        )
    )

    if project is None:
        raise ValueError("Project not found")

    return project


def require_owned_workflow(
    db: Session,
    project_id: UUID,
    workflow_id: UUID,
    user_id: UUID,
) -> Workflow:
    require_owned_project(
        db=db,
        project_id=project_id,
        user_id=user_id,
    )

    workflow = db.scalar(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.project_id == project_id,
        )
    )

    if workflow is None:
        raise ValueError("Workflow not found")

    return workflow


def get_workflows(
    db: Session,
    project_id: UUID,
    user_id: UUID,
) -> list[Workflow]:
    project = require_owned_project(
        db=db,
        project_id=project_id,
        user_id=user_id,
    )

    statement = (
        select(Workflow)
        .where(
            Workflow.project_id == project.id
        )
        .order_by(
            Workflow.created_at.desc()
        )
    )

    workflows = db.scalars(statement).all()

    return list(workflows)


def create_execution(
    db: Session,
    project_id: UUID,
    workflow_id: UUID,
    payload: ExecutionCreate,
    user_id: UUID,
) -> tuple[Execution, bool]:
    workflow = require_owned_workflow(
        db=db,
        project_id=project_id,
        workflow_id=workflow_id,
        user_id=user_id,
    )

    execution, created = create_or_return_existing(
        db=db,
        workflow_id=workflow.id,
        idempotency_key=payload.idempotency_key,
        initial_context=payload.input_data,
    )

    return execution, created


def get_executions(
    db: Session,
    project_id: UUID,
    workflow_id: UUID,
    user_id: UUID,
    status: ExecutionStatus | None = None,
) -> list[Execution]:
    workflow = require_owned_workflow(
        db=db,
        project_id=project_id,
        workflow_id=workflow_id,
        user_id=user_id,
    )

    statement = (
        select(Execution)
        .where(
            Execution.workflow_id == workflow.id
        )
        .order_by(
            Execution.created_at.desc()
        )
    )

    if status is not None:
        statement = statement.where(
            Execution.status == status
        )

    executions = db.scalars(statement).all()

    return list(executions)


def get_execution(
    db: Session,
    execution_id: UUID,
    user_id: UUID,
) -> Execution:
    statement = (
        select(Execution)
        .join(
            Workflow,
            Execution.workflow_id == Workflow.id,
        )
        .join(
            Project,
            Workflow.project_id == Project.id,
        )
        .where(
            Execution.id == execution_id,
            Project.user_id == user_id,
        )
    )

    execution = db.scalar(statement)

    if execution is None:
        raise ValueError("Execution not found")

    return execution
