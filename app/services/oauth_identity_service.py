from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.oauth_connection import OAuthConnection
from app.models.user import User
from app.services.google_identity_service import GoogleIdentity


GOOGLE_PROVIDER = "google"


def resolve_google_identity(
    db: Session,
    identity: GoogleIdentity,
) -> User:
    statement = (
        select(OAuthConnection)
        .where(
            OAuthConnection.provider == GOOGLE_PROVIDER,
            OAuthConnection.provider_subject == identity.subject,
        )
    )

    connection = db.scalar(statement)

    if connection is not None:
        user = connection.user

        user.email = identity.email
        user.display_name = identity.display_name

        db.flush()

        return user

    user = User(
        email=identity.email,
        display_name=identity.display_name,
    )

    db.add(user)
    db.flush()

    connection = OAuthConnection(
        user_id=user.id,
        provider=GOOGLE_PROVIDER,
        provider_subject=identity.subject,
    )

    db.add(connection)
    db.flush()

    return user