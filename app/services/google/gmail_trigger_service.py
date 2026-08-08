from typing import Any
from uuid import UUID

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.services.execution.execution_service import (
    create_or_return_existing,
)

class GmailTriggerError(Exception):
    """Base exception for Gmail trigger failures."""

@dataclass(frozen=True)
class GmailTriggerPayload:
    user_id: UUID
    workflow_id: UUID
    provider_message_id: str
    sender: str
    subject: str
    body_text: str

    def to_context(self) -> dict[str, Any]:
        return {
            "user_id": str(self.user_id),
            "workflow_id": str(self.workflow_id),
            "provider_message_id": self.provider_message_id,
            "sender": self.sender,
            "subject": self.subject,
            "body_text": self.body_text,
        }


def build_gmail_idempotency_key(
    *,
    user_id: UUID,
    provider_message_id: str,
) -> str:
    normalized_message_id = provider_message_id.strip()

    if not normalized_message_id:
        raise GmailTriggerError(
            "Provider message id is required."
        )

    return f"gmail:{user_id}:{normalized_message_id}"


def trigger_email_workflow(
    db: Session,
    *,
    payload: GmailTriggerPayload,
) -> tuple[Execution, bool]:
    idempotency_key = build_gmail_idempotency_key(
        user_id=payload.user_id,
        provider_message_id=payload.provider_message_id,
    )

    return create_or_return_existing(
        db=db,
        workflow_id=payload.workflow_id,
        idempotency_key=idempotency_key,
        initial_context=payload.to_context(),
    )