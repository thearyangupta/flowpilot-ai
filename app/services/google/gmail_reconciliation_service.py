from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.google.gmail_poll_service import (
    GmailMessageReference,
    poll_selected_messages,
)


DEFAULT_RECONCILIATION_WINDOW_MINUTES = 10


def build_reconciliation_query(
    *,
    after: datetime,
) -> str:
    if after.tzinfo is None:
        after = after.replace(tzinfo=timezone.utc)

    after_utc = after.astimezone(timezone.utc)

    timestamp = int(after_utc.timestamp())

    return f"after:{timestamp}"


def reconcile_gmail_messages(
    db: Session,
    *,
    user_id: UUID,
    window_minutes: int = DEFAULT_RECONCILIATION_WINDOW_MINUTES,
) -> tuple[GmailMessageReference, ...]:
    if window_minutes <= 0:
        raise ValueError(
            "window_minutes must be greater than zero."
        )

    after = datetime.now(timezone.utc) - timedelta(
        minutes=window_minutes,
    )

    query = build_reconciliation_query(
        after=after,
    )

    return poll_selected_messages(
        db=db,
        user_id=user_id,
        query=query,
    )