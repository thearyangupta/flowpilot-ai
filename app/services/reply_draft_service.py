from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import ReplyDraftStatus
from app.models.reply_draft import ReplyDraft

from sqlalchemy import select


from app.services.google.google_provider_service import (
    build_gmail_client,
)
from app.services.reply_draft_audit_service import (
    create_reply_draft_audit_event,
)
from app.services.execution.execution_event_service import create_execution_event


class ReplyDraftError(Exception):
    """Base exception for reply-draft failures."""


class ReplyDraftNotFoundError(ReplyDraftError):
    """Raised when a reply draft does not exist."""


class InvalidReplyDraftStateError(ReplyDraftError):
    """Raised when a reply draft cannot transition to the requested state."""


def require_owned_pending(
    db: Session,
    *,
    draft_id: UUID,
    user_id: UUID,
) -> ReplyDraft:
    draft = db.get(ReplyDraft, draft_id)

    if draft is None:
        raise ReplyDraftNotFoundError(
            "Reply draft not found."
        )

    if draft.user_id != user_id:
        raise ReplyDraftNotFoundError(
            "Reply draft not found."
        )

    if draft.status != ReplyDraftStatus.PENDING_APPROVAL:
        raise InvalidReplyDraftStateError(
            "Reply draft is not pending approval."
        )

    return draft


def approve(
    db: Session,
    *,
    draft_id: UUID,
    user_id: UUID,
) -> ReplyDraft:
    draft = require_owned_pending(
        db,
        draft_id=draft_id,
        user_id=user_id,
    )

    draft.status = ReplyDraftStatus.APPROVED
    draft.approved_by = user_id
    draft.approved_at = datetime.now(timezone.utc)

    create_reply_draft_audit_event(
        db=db,
        reply_draft_id=draft.id,
        event_type="approved",
        details={},
        actor="user",
        actor_user_id=user_id,
    )

    db.add(draft)
    db.commit()
    db.refresh(draft)

    return draft


def reject(
    db: Session,
    *,
    draft_id: UUID,
    user_id: UUID,
    reason: str,
) -> ReplyDraft:
    draft = require_owned_pending(
        db,
        draft_id=draft_id,
        user_id=user_id,
    )

    normalized_reason = reason.strip()

    if not normalized_reason:
        raise ValueError(
            "A rejection reason is required."
        )

    draft.status = ReplyDraftStatus.REJECTED

    create_reply_draft_audit_event(
        db=db,
        reply_draft_id=draft.id,
        event_type="rejected",
        details={
            "reason": normalized_reason,
        },
        actor="user",
        actor_user_id=user_id,
    )

    db.add(draft)
    db.commit()
    db.refresh(draft)

    return draft

def get_for_update(
    db: Session,
    *,
    draft_id: UUID,
) -> ReplyDraft:
    draft = db.execute(
        select(ReplyDraft)
        .where(ReplyDraft.id == draft_id)
        .with_for_update()
    ).scalar_one_or_none()

    if draft is None:
        raise ReplyDraftNotFoundError(
            "Reply draft not found."
        )

    return draft



def require_approved_for_send(
    db: Session,
    *,
    draft_id: UUID,
    user_id: UUID,
) -> ReplyDraft:
    draft = get_for_update(
        db,
        draft_id=draft_id,
    )

    if draft.user_id != user_id:
        raise ReplyDraftNotFoundError(
            "Reply draft not found."
        )

    if draft.status != ReplyDraftStatus.APPROVED:
        raise InvalidReplyDraftStateError(
            "Reply draft is not approved for sending."
        )

    return draft


def send_approved(
    db: Session,
    *,
    draft_id: UUID,
    user_id: UUID,
) -> ReplyDraft:
    draft = require_approved_for_send(
        db,
        draft_id=draft_id,
        user_id=user_id,
    )

    gmail = build_gmail_client(
        db=db,
        user_id=user_id,
    )

    try:
        response = (
            gmail.users()
            .drafts()
            .send(
                userId="me",
                body={
                    "id": draft.gmail_draft_id,
                },
            )
            .execute()
        )

    except Exception as error:
        raise ReplyDraftError(
            "Gmail draft could not be sent."
        ) from error

    gmail_message_id = response.get("id")

    if not gmail_message_id:
        raise ReplyDraftError(
            "Gmail did not return a message id."
        )

    draft.gmail_message_id = gmail_message_id
    draft.status = ReplyDraftStatus.SENT

    create_reply_draft_audit_event(
        db=db,
        reply_draft_id=draft.id,
        event_type="sent",
        details={
            "gmail_message_id": gmail_message_id,
        },
        actor="workflow_worker",
        actor_user_id=user_id,
    )

    db.add(draft)
    db.commit()
    db.refresh(draft)

    return draft


def create_pending(
    db: Session,
    *,
    user_id: UUID,
    gmail_draft_id: str,
    source_message: dict,
    draft_message: dict,
) -> ReplyDraft:
    """
    Canonical creation path for reply drafts that require
    human approval.

    All workflow/API creation paths should use this function
    instead of constructing ReplyDraft directly.
    """

    draft = ReplyDraft(
        user_id=user_id,
        gmail_draft_id=gmail_draft_id,
        status=ReplyDraftStatus.PENDING_APPROVAL,
        source_message=source_message,
        draft_message=draft_message,
    )

    db.add(draft)

    # Flush first so draft.id exists before creating
    # the related audit event.
    db.flush()

    create_reply_draft_audit_event(
        db=db,
        reply_draft_id=draft.id,
        event_type="created",
        details={
            "status": ReplyDraftStatus.PENDING_APPROVAL.value,
            "gmail_draft_id": gmail_draft_id,
        },
        actor="workflow_worker",
        actor_user_id=user_id,
    )

    db.commit()
    db.refresh(draft)

    return draft


def list_pending_for_user(
    db: Session,
    user_id: UUID,
) -> list[ReplyDraft]:
    statement = (
        select(ReplyDraft)
        .where(
            ReplyDraft.user_id == user_id,
            ReplyDraft.status
            == ReplyDraftStatus.PENDING_APPROVAL,
        )
        .order_by(
            ReplyDraft.created_at.desc()
        )
    )

    return list(
        db.scalars(statement).all()
    )