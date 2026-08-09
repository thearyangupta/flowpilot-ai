from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.gmail_message import GmailMessage


@dataclass(frozen=True)
class GmailIngestionResult:
    message: GmailMessage
    created: bool


def ingest_gmail_message(
    db: Session,
    *,
    user_id: UUID,
    provider_message_id: str,
    provider_thread_id: str | None,
    sender: str,
    subject: str,
    body_text: str,
    body_hash: str,
) -> GmailIngestionResult:
    normalized_message_id = provider_message_id.strip()

    if not normalized_message_id:
        raise ValueError("Provider message id is required.")

    existing_message = db.scalar(
        select(GmailMessage).where(
            GmailMessage.user_id == user_id,
            GmailMessage.provider_message_id == normalized_message_id,
        )
    )

    if existing_message:
        return GmailIngestionResult(
            message=existing_message,
            created=False,
        )

    message = GmailMessage(
        user_id=user_id,
        provider_message_id=normalized_message_id,
        provider_thread_id=provider_thread_id,
        sender=sender,
        subject=subject,
        body_text=body_text,
        body_hash=body_hash,
    )

    db.add(message)
    db.flush()

    return GmailIngestionResult(
        message=message,
        created=True,
    )