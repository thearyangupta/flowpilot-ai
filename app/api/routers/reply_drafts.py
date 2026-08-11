from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.reply_draft import ReplyDraftRead
from app.services import reply_draft_service
from app.services.reply_draft_service import (
    InvalidReplyDraftStateError,
    ReplyDraftNotFoundError,
)


router = APIRouter()


@router.post(
    "/reply-drafts/{draft_id}/approve",
    response_model=ReplyDraftRead,
)
def approve_reply_draft(
    draft_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReplyDraftRead:
    try:
        return reply_draft_service.approve(
            db=db,
            draft_id=draft_id,
            user_id=current_user.id,
        )

    except ReplyDraftNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except InvalidReplyDraftStateError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.post(
    "/reply-drafts/{draft_id}/reject",
    response_model=ReplyDraftRead,
)
def reject_reply_draft(
    draft_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReplyDraftRead:
    try:
        return reply_draft_service.reject(
            db=db,
            draft_id=draft_id,
            user_id=current_user.id,
        )

    except ReplyDraftNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except InvalidReplyDraftStateError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error