from __future__ import annotations

from uuid import UUID

from app.db.session import SessionLocal
from app.services.reply_draft_service import (
    InvalidReplyDraftStateError,
    ReplyDraftError,
    ReplyDraftNotFoundError,
    StaleReplyDraftRevisionError,
    send_approved,
)
from app.worker.celery_app import celery_app


@celery_app.task(
    name="flowpilot.reply_drafts.send_approved",
)
def send_approved_reply_draft(
    draft_id: str,
    user_id: str,
    expected_revision: int,
) -> None:
    db = SessionLocal()

    try:
        send_approved(
            db=db,
            draft_id=UUID(draft_id),
            user_id=UUID(user_id),
            expected_revision=expected_revision,
        )

    except (
        ReplyDraftNotFoundError,
        InvalidReplyDraftStateError,
        StaleReplyDraftRevisionError,
        ReplyDraftError,
    ):
        db.rollback()
        raise

    finally:
        db.close()