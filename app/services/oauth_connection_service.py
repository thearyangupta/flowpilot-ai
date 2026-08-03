from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.oauth_connection import OAuthConnection


GOOGLE_PROVIDER = "google"


def get_google_connection(
    db: Session,
    *,
    user_id: UUID,
) -> OAuthConnection | None:
    statement = select(OAuthConnection).where(
        OAuthConnection.user_id == user_id,
        OAuthConnection.provider == GOOGLE_PROVIDER,
    )

    return db.scalar(statement)