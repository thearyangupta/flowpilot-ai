from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.oauth_connection import OAuthConnection


GOOGLE_PROVIDER = "google"


class GoogleConnectionNotFoundError(Exception):
    pass


class GoogleIdentityMismatchError(Exception):
    pass


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


def require_google_connection(
    db: Session,
    *,
    user_id: UUID,
) -> OAuthConnection:
    connection = get_google_connection(
        db=db,
        user_id=user_id,
    )

    if connection is None:
        raise GoogleConnectionNotFoundError(
            "Google connection was not found."
        )

    return connection


def ensure_google_identity_matches(
    connection: OAuthConnection,
    *,
    provider_subject: str,
) -> None:
    if connection.provider_subject != provider_subject:
        raise GoogleIdentityMismatchError(
            "Google identity does not match the "
            "existing FlowPilot connection."
        )