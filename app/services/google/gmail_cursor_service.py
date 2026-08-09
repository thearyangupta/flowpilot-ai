from uuid import UUID

from sqlalchemy.orm import Session

from app.models.oauth_connection import OAuthConnection


def save_gmail_history_cursor(
    db: Session,
    *,
    connection: OAuthConnection,
    history_id: str,
) -> OAuthConnection:
    if not history_id.strip():
        raise ValueError(
            "Gmail history id is required."
        )

    connection.gmail_history_id = history_id

    db.add(connection)

    return connection