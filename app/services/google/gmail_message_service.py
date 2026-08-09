from dataclasses import dataclass
from typing import Any
import hashlib

class GmailMessageNormalizationError(Exception):
    """Raised when a Gmail message cannot be normalized."""


@dataclass(frozen=True)
class GmailMessage:
    provider_message_id: str
    provider_thread_id: str | None
    sender: str
    subject: str
    body_text: str

@dataclass(frozen=True)
class GmailMessage:
    provider_message_id: str
    provider_thread_id: str | None
    sender: str
    subject: str
    body_text: str
    body_hash: str


def _decode_body_data(data: str) -> str:
    import base64

    try:
        decoded = base64.urlsafe_b64decode(
            data + "=" * (-len(data) % 4)
        )
        return decoded.decode("utf-8", errors="replace")
    except Exception as error:
        raise GmailMessageNormalizationError(
            "Gmail message body could not be decoded."
        ) from error


def _extract_text_from_payload(payload: dict[str, Any]) -> str:
    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {})

    if mime_type == "text/plain":
        data = body.get("data")
        if data:
            return _decode_body_data(data)

    for part in payload.get("parts", []):
        text = _extract_text_from_payload(part)
        if text:
            return text

    return ""


def normalize_gmail_message(
    raw_message: dict[str, Any],
) -> GmailMessage:
    provider_message_id = raw_message.get("id")

    if not provider_message_id:
        raise GmailMessageNormalizationError(
            "Gmail message id is required."
        )

    payload = raw_message.get("payload", {})

    headers = {
        header.get("name", "").lower(): header.get("value", "")
        for header in payload.get("headers", [])
    }

    sender = headers.get("from", "").strip()
    subject = headers.get("subject", "").strip()

    body_text = _extract_text_from_payload(payload).strip()
    body_hash = hashlib.sha256(
        body_text.encode("utf-8")
    ).hexdigest()

    return GmailMessage(
        provider_message_id=provider_message_id,
        provider_thread_id=raw_message.get("threadId"),
        sender=sender,
        subject=subject,
        body_text=body_text,
        body_hash=body_hash,
    )