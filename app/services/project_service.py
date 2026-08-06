from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ExecutionStatus
from app.models.execution import Execution
from app.models.project import Project
from app.models.workflow import Workflow
from app.schemas.execution import ExecutionCreate
from app.schemas.project import ProjectCreate
from app.services.execution.execution_service import create_or_return_existing


def create(
    db: Session,
    payload: ProjectCreate,
) -> Project:
    project = Project(**payload.model_dump())

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


def get_all(db: Session) -> list[Project]:
    statement = select(Project).order_by(
        Project.created_at.desc()
    )

    projects = db.scalars(statement).all()

    return list(projects)


def create_execution(
    db: Session,
    project_id: UUID,
    workflow_id: UUID,
    payload: ExecutionCreate,
) -> tuple[Execution, bool]:
    project = db.get(Project, project_id)

    if project is None:
        raise ValueError("Project not found")

    workflow = db.get(Workflow, workflow_id)

    if workflow is None:
        raise ValueError("Workflow not found")

    if workflow.project_id != project.id:
        raise ValueError(
            "Workflow does not belong to this project"
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
    status: ExecutionStatus | None = None,
) -> list[Execution]:
    project = db.get(Project, project_id)

    if project is None:
        raise ValueError("Project not found")

    workflow = db.get(Workflow, workflow_id)

    if workflow is None:
        raise ValueError("Workflow not found")

    if workflow.project_id != project.id:
        raise ValueError(
            "Workflow does not belong to this project"
        )

    statement = (
        select(Execution)
        .where(Execution.workflow_id == workflow.id)
        .order_by(Execution.created_at.desc())
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
) -> Execution:
    execution = db.get(
        Execution,
        execution_id,
    )

    if execution is None:
        raise ValueError("Execution not found")

    return execution