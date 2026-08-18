from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
)
from app.schemas.workflow import (
    WorkflowRead,
    WorkflowTemplateCreate,
)
from app.services import (
    project_service,
    workflow_definition,
)
from app.services.workflow_template_service import (
    UnsupportedWorkflowTemplateError,
    build_workflow_from_template,
)


router = APIRouter()


@router.get(
    "/projects",
    response_model=list[ProjectRead],
)
def list_projects(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> list[ProjectRead]:
    return project_service.get_all(
        db=db,
        user_id=current_user.id,
    )


@router.post(
    "/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> ProjectRead:
    return project_service.create(
        db=db,
        payload=payload,
        user_id=current_user.id,
    )


@router.get(
    "/projects/{project_id}/workflows",
    response_model=list[WorkflowRead],
)
def list_workflows(
    project_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> list[WorkflowRead]:
    try:
        return project_service.get_workflows(
            db=db,
            project_id=project_id,
            user_id=current_user.id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error


@router.post(
    "/projects/{project_id}/workflows",
    response_model=WorkflowRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow(
    project_id: UUID,
    payload: WorkflowTemplateCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> WorkflowRead:
    try:
        workflow_payload = (
            build_workflow_from_template(
                name=payload.name,
                template_id=payload.template,
            )
        )

        return (
            workflow_definition
            .create_workflow_definition(
                db=db,
                project_id=project_id,
                user_id=current_user.id,
                payload=workflow_payload,
            )
        )

    except UnsupportedWorkflowTemplateError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except ValueError as error:
        if str(error) == "Project not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            ) from error

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error