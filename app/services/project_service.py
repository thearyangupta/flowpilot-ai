from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.workflow import Workflow
from app.schemas.project import ProjectCreate
from app.schemas.workflow import WorkflowCreate
from app.models.execution import Execution
from app.models.enums import ExecutionStatus


def create(db: Session, payload: ProjectCreate) -> Project:
    project = Project(**payload.model_dump())

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


def get_all(db: Session) -> list[Project]:
    statement = select(Project).order_by(Project.created_at.desc())

    projects = db.scalars(statement).all()

    return list(projects)


def create_workflow(
    db: Session,
    project_id: UUID,
    payload: WorkflowCreate,
) -> Workflow:
    project = db.get(Project, project_id)

    if project is None:
        raise ValueError("Project not found")

    workflow = Workflow(
        project_id=project.id,
        **payload.model_dump(),
    )

    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    return workflow


def create_execution(
    db: Session,
    project_id: UUID,
    workflow_id: UUID,
) -> Execution:
    project = db.get(Project, project_id)

    if project is None:
        raise ValueError("Project not found")

    workflow = db.get(Workflow, workflow_id)

    if workflow is None:
        raise ValueError("Workflow not found")

    if workflow.project_id != project.id:
        raise ValueError("Workflow does not belong to this project")

    execution = Execution(
        workflow_id=workflow.id,
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    return execution

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
        raise ValueError("Workflow does not belong to this project")

    statement = (
        select(Execution)
        .where(Execution.workflow_id == workflow.id)
        .order_by(Execution.created_at.desc())
    )

    if status is not None:
        statement = statement.where(Execution.status == status)

    executions = db.scalars(statement).all()

    return list(executions)