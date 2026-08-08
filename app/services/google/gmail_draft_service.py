from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.google.google_provider_service import (
    build_gmail_client,
)
from email.message import EmailMessage
import base64


class GmailDraftCreationError(Exception):
    """Raised when a Gmail draft cannot be created."""


def build_reply_message(
    *,
    recipient: str,
    subject: str,
    body: str,
    in_reply_to: str,
    references: str | None = None,
) -> EmailMessage:
    message = EmailMessage()

    message["To"] = recipient
    message["Subject"] = subject
    message["In-Reply-To"] = in_reply_to

    if references:
        message["References"] = references

    message.set_content(body)

    return message


def serialize_reply_message(
    message: EmailMessage,
) -> bytes:
    return message.as_bytes()


def encode_raw_message(
    message: EmailMessage,
) -> str:
    raw_bytes = message.as_bytes()

    return base64.urlsafe_b64encode(
        raw_bytes,
    ).decode("ascii")




def create_gmail_draft(
    db: Session,
    *,
    user_id: UUID,
    message: EmailMessage,
) -> dict[str, Any]:
    gmail = build_gmail_client(
        db=db,
        user_id=user_id,
    )

    encoded_message = encode_raw_message(message)

    try:
        response: dict[str, Any] = (
            gmail.users()
            .drafts()
            .create(
                userId="me",
                body={
                    "message": {
                        "raw": encoded_message,
                    },
                },
            )
            .execute()
        )

    except Exception as error:
        raise GmailDraftCreationError(
            "Gmail draft could not be created."
        ) from error

    return response