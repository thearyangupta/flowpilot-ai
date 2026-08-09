from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.services.google.google_provider_service import (
    build_gmail_client,
)


class GmailWatchError(Exception):
    """Base exception for Gmail watch failures."""


@dataclass(frozen=True)
class GmailWatch:
    history_id: str
    expiration: datetime | None


def start_gmail_watch(
    db: Session,
    *,
    user_id,
    topic_name: str,
) -> GmailWatch:
    if not topic_name.strip():
        raise GmailWatchError(
            "Pub/Sub topic name is required."
        )

    gmail = build_gmail_client(
        db=db,
        user_id=user_id,
    )

    try:
        response: dict[str, Any] = (
            gmail.users()
            .watch(
                userId="me",
                body={
                    "topicName": topic_name,
                    "labelIds": ["INBOX"],
                },
            )
            .execute()
        )

    except Exception as error:
        raise GmailWatchError(
            "Gmail watch could not be started."
        ) from error

    history_id = response.get("historyId")

    if not isinstance(history_id, str) or not history_id:
        raise GmailWatchError(
            "Gmail watch did not return a history id."
        )

    expiration_raw = response.get("expiration")

    expiration = None

    if expiration_raw is not None:
        try:
            expiration = datetime.fromtimestamp(
                int(expiration_raw) / 1000,
            )
        except (TypeError, ValueError, OverflowError) as error:
            raise GmailWatchError(
                "Gmail watch returned an invalid expiration."
            ) from error

    return GmailWatch(
        history_id=history_id,
        expiration=expiration,
    )