from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approval_decision import ApprovalDecision
from app.models.enums import ReplyDraftStatus
from app.models.reply_draft import ReplyDraft
from app.models.reply_draft_revision import ReplyDraftRevision
from app.services.execution.execution_event_service import (
    create_execution_event,
)
from app.services.google.google_provider_service import (
    build_gmail_client,
)
from app.services.reply_draft_audit_service import (
    create_reply_draft_audit_event,
)
from app.services.reply_draft_revision_service import (
    ReplyDraftRevisionNotFoundError,
    create_revision_record,
    get_revision_for_user,
    hash_content,
)


class ReplyDraftError(Exception):
    """Base exception for reply-draft failures."""


class ReplyDraftNotFoundError(ReplyDraftError):
    """Raised when a reply draft does not exist."""


class InvalidReplyDraftStateError(ReplyDraftError):
    """Raised when a reply draft cannot transition to the requested state."""


def require_owned(
    db: Session,
    *,
    draft_id: UUID,
    user_id: UUID,
) -> ReplyDraft:
    draft = db.get(ReplyDraft, draft_id)

    if draft is None or draft.user_id != user_id:
        # Do not reveal whether another user's resource exists.
        raise ReplyDraftNotFoundError(
            "Reply draft not found."
        )

    return draft


def require_owned_pending(
    db: Session,
    *,
    draft_id: UUID,
    user_id: UUID,
) -> ReplyDraft:
    draft = require_owned(
        db,
        draft_id=draft_id,
        user_id=user_id,
    )

    if draft.status != ReplyDraftStatus.PENDING_APPROVAL:
        raise InvalidReplyDraftStateError(
            "Reply draft is not pending approval."
        )

    return draft


def get_current_revision(
    db: Session,
    *,
    draft: ReplyDraft,
) -> ReplyDraftRevision:
    try:
        return get_revision_for_user(
            db,
            reply_draft_id=draft.id,
            user_id=draft.user_id,
            revision_number=draft.current_revision_number,
        )
    except ReplyDraftRevisionNotFoundError as error:
        raise ReplyDraftError(
            "Current reply draft revision is missing."
        ) from error


def create_approval_decision(
    db: Session,
    *,
    user_id: UUID,
    revision_id: UUID,
    actor_user_id: UUID,
    action: str,
    reason: str | None,
) -> ApprovalDecision:
    decision = ApprovalDecision(
        user_id=user_id,
        revision_id=revision_id,
        actor_user_id=actor_user_id,
        action=action,
        reason=reason,
    )

    db.add(decision)
    db.flush()

    return decision


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

    revision = get_current_revision(
        db,
        draft=draft,
    )

    create_approval_decision(
        db=db,
        user_id=user_id,
        revision_id=revision.id,
        actor_user_id=user_id,
        action="approved",
        reason=None,
    )

    draft.status = ReplyDraftStatus.APPROVED
    draft.approved_by = user_id
    draft.approved_at = datetime.now(timezone.utc)

    create_reply_draft_audit_event(
        db=db,
        reply_draft_id=draft.id,
        event_type="approved",
        details={
            "revision_id": str(revision.id),
            "revision_number": revision.revision_number,
            "content_hash": revision.content_hash,
        },
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

    revision = get_current_revision(
        db,
        draft=draft,
    )

    create_approval_decision(
        db=db,
        user_id=user_id,
        revision_id=revision.id,
        actor_user_id=user_id,
        action="rejected",
        reason=normalized_reason,
    )

    draft.status = ReplyDraftStatus.REJECTED
    draft.approved_by = None
    draft.approved_at = None

    create_reply_draft_audit_event(
        db=db,
        reply_draft_id=draft.id,
        event_type="rejected",
        details={
            "reason": normalized_reason,
            "revision_id": str(revision.id),
            "revision_number": revision.revision_number,
            "content_hash": revision.content_hash,
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


def create_revision(
    db: Session,
    *,
    draft_id: UUID,
    user_id: UUID,
    content: dict[str, Any],
    created_by_actor: str = "user",
    created_by_user_id: UUID | None = None,
) -> ReplyDraftRevision:
    """
    Append a new immutable revision.

    This is intentionally a service boundary rather than an ORM update.
    Day 2 will add expected-revision optimistic concurrency to the
    user-facing edit command.
    """
    draft = get_for_update(
        db,
        draft_id=draft_id,
    )

    if draft.user_id != user_id:
        raise ReplyDraftNotFoundError(
            "Reply draft not found."
        )

    if draft.status == ReplyDraftStatus.SENT:
        raise InvalidReplyDraftStateError(
            "A sent reply draft cannot be revised."
        )

    next_revision_number = (
        draft.current_revision_number + 1
    )

    revision = create_revision_record(
        db=db,
        reply_draft_id=draft.id,
        user_id=user_id,
        revision_number=next_revision_number,
        content=content,
        created_by_actor=created_by_actor,
        created_by_user_id=(
            created_by_user_id
            if created_by_user_id is not None
            else user_id
        ),
    )

    # Mutable summary only. Historical authority lives in revisions.
    draft.draft_message = content
    draft.current_revision_number = next_revision_number

    # New content has not been reviewed yet.
    draft.status = ReplyDraftStatus.PENDING_APPROVAL
    draft.approved_by = None
    draft.approved_at = None

    create_reply_draft_audit_event(
        db=db,
        reply_draft_id=draft.id,
        event_type="revision_created",
        details={
            "revision_id": str(revision.id),
            "revision_number": revision.revision_number,
            "content_hash": revision.content_hash,
        },
        actor=created_by_actor,
        actor_user_id=created_by_user_id or user_id,
    )

    db.add(draft)
    db.commit()
    db.refresh(revision)

    return revision


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

    revision = get_current_revision(
        db,
        draft=draft,
    )

    latest_decision = db.execute(
        select(ApprovalDecision)
        .where(
            ApprovalDecision.user_id == user_id,
            ApprovalDecision.revision_id == revision.id,
        )
        .order_by(
            ApprovalDecision.created_at.desc(),
            ApprovalDecision.id.desc(),
        )
        .limit(1)
    ).scalar_one_or_none()

    if (
        latest_decision is None
        or latest_decision.action != "approved"
    ):
        raise InvalidReplyDraftStateError(
            "The current revision has no valid approval decision."
        )

    # Fail closed if mutable compatibility state drifted away
    # from the exact approved revision.
    if hash_content(draft.draft_message) != revision.content_hash:
        raise InvalidReplyDraftStateError(
            "Current draft content does not match the approved revision."
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
            "revision_number": draft.current_revision_number,
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
    Canonical creation path for reply drafts that require human approval.
    """
    draft = ReplyDraft(
        user_id=user_id,
        gmail_draft_id=gmail_draft_id,
        status=ReplyDraftStatus.PENDING_APPROVAL,
        current_revision_number=1,
        source_message=source_message,
        draft_message=draft_message,
    )

    db.add(draft)
    db.flush()

    revision = create_revision_record(
        db=db,
        reply_draft_id=draft.id,
        user_id=user_id,
        revision_number=1,
        content=draft_message,
        created_by_actor="workflow_worker",
        created_by_user_id=user_id,
    )

    create_reply_draft_audit_event(
        db=db,
        reply_draft_id=draft.id,
        event_type="created",
        details={
            "status": ReplyDraftStatus.PENDING_APPROVAL.value,
            "gmail_draft_id": gmail_draft_id,
            "revision_id": str(revision.id),
            "revision_number": revision.revision_number,
            "content_hash": revision.content_hash,
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


def get_approval_bundle(
    db: Session,
    *,
    draft_id: UUID,
    user_id: UUID,
    revision_number: int | None = None,
) -> dict[str, Any]:
    draft = require_owned(
        db,
        draft_id=draft_id,
        user_id=user_id,
    )

    target_revision_number = (
        revision_number
        if revision_number is not None
        else draft.current_revision_number
    )

    try:
        revision = get_revision_for_user(
            db,
            reply_draft_id=draft.id,
            user_id=user_id,
            revision_number=target_revision_number,
        )
    except ReplyDraftRevisionNotFoundError as error:
        raise ReplyDraftNotFoundError(
            "Reply draft revision not found."
        ) from error

    decisions = list(
        db.scalars(
            select(ApprovalDecision)
            .where(
                ApprovalDecision.user_id == user_id,
                ApprovalDecision.revision_id == revision.id,
            )
            .order_by(
                ApprovalDecision.created_at.asc(),
                ApprovalDecision.id.asc(),
            )
        ).all()
    )

    return {
        "draft_id": draft.id,
        "status": draft.status,
        "current_revision_number": draft.current_revision_number,
        "revision": revision,
        "decisions": decisions,
    }
