from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.public_errors import (
    GMAIL_IDEMPOTENCY_CONFLICT,
    GMAIL_SEND_IN_PROGRESS,
    GMAIL_SEND_OUTCOME_UNCERTAIN,
    REPLY_DRAFT_INVALID_STATE,
    REPLY_DRAFT_NOT_FOUND,
    REPLY_DRAFT_STALE,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.reply_draft import (
    ReplyDraftApprovalBundleRead,
    ReplyDraftDecisionCreate,
    ReplyDraftEditCreate,
    ReplyDraftRead,
    ReplyDraftRejectCreate,
    ReplyDraftRevisionRead,
    ReplyDraftSendCreate,
)
from app.services import reply_draft_service
from app.services.google.gmail_command_service import (
    GmailCommandConflictError,
    GmailCommandInProgressError,
    GmailCommandOutcomeUncertainError,
)
from app.services.reply_draft_service import (
    InvalidReplyDraftStateError,
    ReplyDraftNotFoundError,
    StaleReplyDraftRevisionError,
)
from app.worker.reply_draft_tasks import (
    send_approved_reply_draft,
)

router = APIRouter()


def raise_conflict(
    error: Exception,
) -> None:
    if isinstance(
        error,
        StaleReplyDraftRevisionError,
    ):
        public_message = REPLY_DRAFT_STALE
    else:
        public_message = (
            REPLY_DRAFT_INVALID_STATE
        )

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=public_message,
    ) from error


@router.get(
    "/reply-drafts",
    response_model=list[ReplyDraftRead],
)
def list_pending_reply_drafts(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> list[ReplyDraftRead]:
    return (
        reply_draft_service
        .list_pending_for_user(
            db=db,
            user_id=current_user.id,
        )
    )


@router.get(
    "/reply-drafts/{draft_id}/approval-bundle",
    response_model=(
        ReplyDraftApprovalBundleRead
    ),
)
def get_reply_draft_approval_bundle(
    draft_id: UUID,
    revision_number: int | None = Query(
        default=None,
        ge=1,
    ),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> ReplyDraftApprovalBundleRead:
    try:
        return (
            reply_draft_service
            .get_approval_bundle(
                db=db,
                draft_id=draft_id,
                user_id=current_user.id,
                revision_number=(
                    revision_number
                ),
            )
        )

    except ReplyDraftNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=REPLY_DRAFT_NOT_FOUND,
        ) from error


@router.post(
    "/reply-drafts/{draft_id}/revisions",
    response_model=ReplyDraftRevisionRead,
)
def edit_reply_draft(
    draft_id: UUID,
    payload: ReplyDraftEditCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> ReplyDraftRevisionRead:
    try:
        return (
            reply_draft_service
            .create_revision(
                db=db,
                draft_id=draft_id,
                user_id=current_user.id,
                expected_revision=(
                    payload.expected_revision
                ),
                content=payload.content,
                created_by_actor="user",
                created_by_user_id=(
                    current_user.id
                ),
            )
        )

    except ReplyDraftNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=REPLY_DRAFT_NOT_FOUND,
        ) from error

    except (
        StaleReplyDraftRevisionError,
        InvalidReplyDraftStateError,
    ) as error:
        raise_conflict(error)


@router.post(
    "/reply-drafts/{draft_id}/approve",
    response_model=ReplyDraftRead,
)
def approve_reply_draft(
    draft_id: UUID,
    payload: ReplyDraftDecisionCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> ReplyDraftRead:
    try:
        draft = (
            reply_draft_service
            .approve(
                db=db,
                draft_id=draft_id,
                user_id=current_user.id,
                expected_revision=(
                    payload.expected_revision
                ),
            )
        )

        send_approved_reply_draft.delay(
            str(draft.id),
            str(current_user.id),
            draft.current_revision_number,
        )

        return draft

    except ReplyDraftNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=REPLY_DRAFT_NOT_FOUND,
        ) from error

    except (
        StaleReplyDraftRevisionError,
        InvalidReplyDraftStateError,
    ) as error:
        raise_conflict(error)


@router.post(
    "/reply-drafts/{draft_id}/reject",
    response_model=ReplyDraftRead,
)
def reject_reply_draft(
    draft_id: UUID,
    payload: ReplyDraftRejectCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> ReplyDraftRead:
    try:
        return (
            reply_draft_service
            .reject(
                db=db,
                draft_id=draft_id,
                user_id=current_user.id,
                expected_revision=(
                    payload.expected_revision
                ),
                reason=payload.reason,
            )
        )

    except ReplyDraftNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=REPLY_DRAFT_NOT_FOUND,
        ) from error

    except (
        StaleReplyDraftRevisionError,
        InvalidReplyDraftStateError,
    ) as error:
        raise_conflict(error)


@router.post(
    "/reply-drafts/{draft_id}/send",
    response_model=ReplyDraftRead,
)
def send_reply_draft(
    draft_id: UUID,
    payload: ReplyDraftSendCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> ReplyDraftRead:
    try:
        return (
            reply_draft_service
            .send_approved(
                db=db,
                draft_id=draft_id,
                user_id=current_user.id,
                expected_revision=(
                    payload.expected_revision
                ),
                idempotency_key=(
                    payload.idempotency_key
                ),
            )
        )

    except ReplyDraftNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=REPLY_DRAFT_NOT_FOUND,
        ) from error

    except GmailCommandConflictError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                GMAIL_IDEMPOTENCY_CONFLICT
            ),
        ) from error

    except GmailCommandInProgressError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=GMAIL_SEND_IN_PROGRESS,
        ) from error

    except (
        GmailCommandOutcomeUncertainError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                GMAIL_SEND_OUTCOME_UNCERTAIN
            ),
        ) from error

    except (
        StaleReplyDraftRevisionError,
        InvalidReplyDraftStateError,
    ) as error:
        raise_conflict(error)