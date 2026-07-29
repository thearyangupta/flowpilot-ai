from fastapi import APIRouter, Depends, status , HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectRead
from app.services import project_service,execution_service
from app.schemas.workflow import WorkflowCreate, WorkflowRead
from app.schemas.execution import ExecutionCreate, ExecutionRead, ExecutionDetail,ExecutionEventRead
from app.models.enums import ExecutionStatus
from app.services import workflow_definition
from sqlalchemy import text

router = APIRouter()


@router.get("/db-check", tags=["system"])
def database_check(
    db: Session = Depends(get_db),#depends - This endpoint needs something before it can run.Before running this endpoint, call get_db() and use the yielded value as db
) -> dict[str, str]:
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }

@router.post(
    "/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
):
    return project_service.create(db, payload)


@router.post(
    "/projects/{project_id}/workflows",
    response_model=WorkflowRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow(
    project_id: UUID,
    payload: WorkflowCreate,
    db: Session = Depends(get_db),
):
    try:
        return workflow_definition.create_workflow_definition(
            db=db,
            project_id=project_id,
            payload=payload,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    

@router.post(
    "/projects/{project_id}/workflows/{workflow_id}/executions",
    response_model=ExecutionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_execution(
    project_id: UUID,
    workflow_id: UUID,
    payload: ExecutionCreate,
    db: Session = Depends(get_db),
):
    try:
        return project_service.create_execution(
            db=db,
            project_id=project_id,
            workflow_id=workflow_id,
            payload=payload,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    
@router.get(
    "/projects/{project_id}/workflows/{workflow_id}/executions",
    response_model=list[ExecutionRead],
)
def list_executions(
    project_id: UUID,
    workflow_id: UUID,
    execution_status: ExecutionStatus | None = None,
    db: Session = Depends(get_db),
):
    try:
        return project_service.get_executions(
            db=db,
            project_id=project_id,
            workflow_id=workflow_id,
            status=execution_status,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.get(
    "/executions/{execution_id}",
    response_model=ExecutionDetail,
)
def get_execution_detail(
    execution_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return project_service.get_execution(
            db=db,
            execution_id=execution_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.get(
    "/executions/{execution_id}/events",
    response_model=list[ExecutionEventRead],
)
def get_execution_events(
    execution_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return execution_service.get_execution_events(
            db=db,
            execution_id=execution_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error