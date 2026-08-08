from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.reply_draft_audit_event import ReplyDraftAuditEvent


def create_reply_draft_audit_event(
    db: Session,
    *,
    reply_draft_id: UUID,
    event_type: str,
    details: dict[str, Any] | None = None,
    actor: str | None = None,
    actor_user_id: UUID | None = None,
) -> ReplyDraftAuditEvent:
    event = ReplyDraftAuditEvent(
        reply_draft_id=reply_draft_id,
        event_type=event_type,
        details=details or {},
        actor=actor,
        actor_user_id=actor_user_id,
    )

    db.add(event)

    return event