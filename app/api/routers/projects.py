from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectRead
from app.schemas.workflow import WorkflowCreate, WorkflowRead
from app.services import project_service, workflow_definition


router = APIRouter()


@router.post(
    "/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
):
    return project_service.create(
        db=db,
        payload=payload,
    )


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