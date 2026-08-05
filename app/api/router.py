from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
    Query,
)
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ExecutionNotFoundError,
    ExecutionStillActiveError,
    IdempotencyConflictError,
    RecoveryNotAllowedError,
)
from app.db.session import get_db
from app.models.enums import ExecutionStatus
from app.schemas.execution import (
    ExecutionCreate,
    ExecutionDetail,
    ExecutionEventRead,
    ExecutionRead,
)
from app.schemas.project import ProjectCreate, ProjectRead
from app.schemas.workflow import WorkflowCreate, WorkflowRead
from app.services import (
    execution_service,
    project_service,
    workflow_definition,
    workflow_runner,
)
from app.services.execution_event_service import (
    create_execution_event,
)
from app.services.execution_recovery_service import (
    require_recoverable_execution,
)
from app.worker.tasks import run_execution_task

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserRead


from app.core.cipher import get_token_cipher
from app.schemas.auth import (
    GoogleOAuthCallbackRead,
    GoogleOAuthStartRead,
)
from app.services.oauth_callback_service import (
    OAuthCallbackError,
    complete_google_oauth_callback,
)
from app.services.oauth_start_service import (
    OAuthStartError,
    create_google_oauth_start,
)

from app.core.oauth import (
    GOOGLE_IDENTITY_SCOPES,
    OAuthPurpose,
)

router = APIRouter()


@router.get("/db-check", tags=["system"])
def database_check(
    db: Session = Depends(get_db),
) -> dict[str, str]:
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }


@router.get(
    "/auth/google/start",
    response_model=GoogleOAuthStartRead,
    tags=["authentication"],
)
def start_google_oauth(
    db: Session = Depends(get_db),
) -> GoogleOAuthStartRead:
    try:
        result = create_google_oauth_start(
            db=db,
            cipher=get_token_cipher(),
            purpose=OAuthPurpose.LOGIN,
            requested_scopes=GOOGLE_IDENTITY_SCOPES,
        )

        db.commit()

        return GoogleOAuthStartRead(
            authorization_url=result.authorization_url,
            expires_at=result.expires_at,
        )

    except OAuthStartError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authorization could not be started.",
        ) from error


@router.get(
    "/auth/google/callback",
    response_model=GoogleOAuthCallbackRead,
    tags=["authentication"],
)
def finish_google_oauth(
    code: str | None = None,
    state_value: str | None = Query(
        default=None,
        alias="state",
    ),
    error: str | None = None,
    db: Session = Depends(get_db),
) -> GoogleOAuthCallbackRead:
    if error is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google authorization was not completed.",
        )

    if not code or not state_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Google authorization code and state are required."
            ),
        )

    try:
        result = complete_google_oauth_callback(
            db=db,
            code=code,
            state=state_value,
            cipher=get_token_cipher(),
        )

        db.commit()

        return GoogleOAuthCallbackRead(
            access_token=result.flowpilot_access_token,
            user=result.user,
        )

    except OAuthCallbackError as callback_error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Google OAuth callback could not be completed."
            ),
        ) from callback_error



@router.get(
    "/me",
    response_model=UserRead,
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user



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


@router.post(
    "/projects/{project_id}/workflows/{workflow_id}/executions",
    response_model=ExecutionRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_execution(
    project_id: UUID,
    workflow_id: UUID,
    payload: ExecutionCreate,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        execution, created = project_service.create_execution(
            db=db,
            project_id=project_id,
            workflow_id=workflow_id,
            payload=payload,
        )

        if not created:
            response.status_code = status.HTTP_200_OK
            return execution

        try:
            run_execution_task.delay(
                str(execution.id)
            )

        except Exception as error:
            create_execution_event(
                db=db,
                execution_id=execution.id,
                event_type="execution.publish_failed",
                details={
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                },
                actor="api",
            )

            db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_503_SERVICE_UNAVAILABLE
                ),
                detail=(
                    "Execution was created, but it could "
                    "not be published to the worker queue"
                ),
            ) from error

        return execution

    except IdempotencyConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

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


@router.post("/executions/{execution_id}/resume")
def resume_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        execution = require_recoverable_execution(
            db=db,
            execution_id=execution_id,
        )

        return workflow_runner.resume(
            db=db,
            execution=execution,
        )

    except ExecutionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except (
        ExecutionStillActiveError,
        RecoveryNotAllowedError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error