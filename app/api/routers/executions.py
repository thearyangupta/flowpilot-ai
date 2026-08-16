from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
)
from app.core.config import get_settings
from app.core.exceptions import (
    ExecutionNotFoundError,
    ExecutionStillActiveError,
    IdempotencyConflictError,
    RecoveryNotAllowedError,
)
from app.core.public_errors import (
    EXECUTION_IDEMPOTENCY_CONFLICT,
    EXECUTION_RECOVERY_NOT_ALLOWED,
    EXECUTION_STILL_ACTIVE,
    RATE_LIMIT_EXCEEDED,
    RATE_LIMIT_UNAVAILABLE,
)
from app.core.rate_limit import (
    RateLimitExceeded,
    RateLimitUnavailable,
    enforce_rate_limit,
)
from app.db.session import get_db
from app.models.enums import ExecutionStatus
from app.models.user import User
from app.schemas.execution import (
    ExecutionCreate,
    ExecutionDetail,
    ExecutionEventRead,
    ExecutionRead,
)
from app.services import (
    project_service,
    workflow_runner,
)
from app.services.execution import (
    execution_service,
)
from app.services.execution.execution_event_service import (
    create_execution_event,
)
from app.services.execution.execution_recovery_service import (
    require_recoverable_execution_for_user,
)
from app.worker.tasks import (
    run_execution_task,
)


router = APIRouter()


@router.post(
    "/projects/{project_id}/workflows/"
    "{workflow_id}/executions",
    response_model=ExecutionRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_execution(
    project_id: UUID,
    workflow_id: UUID,
    payload: ExecutionCreate,
    response: Response,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> ExecutionRead:
    settings = get_settings()

    try:
        enforce_rate_limit(
            user_id=current_user.id,
            route_name="execution:create",
            limit=(
                settings
                .execution_create_rate_limit
            ),
            window_seconds=(
                settings
                .execution_create_rate_window_seconds
            ),
        )

    except RateLimitExceeded as error:
        raise HTTPException(
            status_code=(
                status.HTTP_429_TOO_MANY_REQUESTS
            ),
            detail=RATE_LIMIT_EXCEEDED,
            headers={
                "Retry-After": str(
                    error.retry_after
                ),
            },
        ) from error

    except RateLimitUnavailable as error:
        raise HTTPException(
            status_code=(
                status
                .HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=RATE_LIMIT_UNAVAILABLE,
        ) from error

    try:
        execution, created = (
            project_service.create_execution(
                db=db,
                project_id=project_id,
                workflow_id=workflow_id,
                payload=payload,
                user_id=current_user.id,
            )
        )

        if not created:
            response.status_code = (
                status.HTTP_200_OK
            )

            return execution

        try:
            run_execution_task.delay(
                str(execution.id)
            )

        except Exception as error:
            create_execution_event(
                db=db,
                execution_id=execution.id,
                event_type=(
                    "execution.publish_failed"
                ),
                details={
                    "error_type":
                        type(error).__name__,
                    "error_message":
                        str(error),
                },
                actor="api",
            )

            db.commit()

            raise HTTPException(
                status_code=(
                    status
                    .HTTP_503_SERVICE_UNAVAILABLE
                ),
                detail=(
                    "Execution was created, "
                    "but it could not be "
                    "published to the worker queue"
                ),
            ) from error

        return execution

    except IdempotencyConflictError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                EXECUTION_IDEMPOTENCY_CONFLICT
            ),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Project or workflow not found"
            ),
        ) from error


@router.get(
    "/projects/{project_id}/workflows/"
    "{workflow_id}/executions",
    response_model=list[ExecutionRead],
)
def list_executions(
    project_id: UUID,
    workflow_id: UUID,
    execution_status:
        ExecutionStatus | None = None,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> list[ExecutionRead]:
    try:
        return project_service.get_executions(
            db=db,
            project_id=project_id,
            workflow_id=workflow_id,
            user_id=current_user.id,
            status=execution_status,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Project or workflow not found"
            ),
        ) from error


@router.get(
    "/executions/{execution_id}",
    response_model=ExecutionDetail,
)
def get_execution_detail(
    execution_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> ExecutionDetail:
    try:
        return (
            project_service.get_execution(
                db=db,
                execution_id=execution_id,
                user_id=current_user.id,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Execution not found",
        ) from error


@router.get(
    "/executions/{execution_id}/events",
    response_model=list[ExecutionEventRead],
)
def get_execution_events(
    execution_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> list[ExecutionEventRead]:
    try:
        return (
            execution_service
            .get_execution_events_for_user(
                db=db,
                execution_id=execution_id,
                user_id=current_user.id,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Execution not found",
        ) from error


@router.post(
    "/executions/{execution_id}/resume",
)
def resume_execution(
    execution_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    try:
        execution = (
            require_recoverable_execution_for_user(
                db=db,
                execution_id=execution_id,
                user_id=current_user.id,
            )
        )

        return workflow_runner.resume(
            db=db,
            execution=execution,
        )

    except ExecutionNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Execution not found",
        ) from error

    except ExecutionStillActiveError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=EXECUTION_STILL_ACTIVE,
        ) from error

    except RecoveryNotAllowedError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                EXECUTION_RECOVERY_NOT_ALLOWED
            ),
        ) from error