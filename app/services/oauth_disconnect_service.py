from sqlalchemy.orm import Session

from app.core.cipher import TextCipher
from app.models.oauth_connection import OAuthConnection
from app.services.google_oauth_service import (
    GoogleOAuthRevocationError,
    revoke_google_token,
)
from app.services.oauth_credentials_service import (
    decrypt_access_token,
    decrypt_refresh_token,
)


def disconnect_google_connection(
    db: Session,
    *,
    connection: OAuthConnection,
    cipher: TextCipher,
) -> bool:
    token: str | None = None

    try:
        if connection.refresh_token_ciphertext is not None:
            token = decrypt_refresh_token(
                connection,
                cipher,
            )
        elif connection.access_token_ciphertext is not None:
            token = decrypt_access_token(
                connection,
                cipher,
            )

        if token is not None:
            revoke_google_token(token)

        revoked_remotely = True

    except (
        GoogleOAuthRevocationError,
        ValueError,
    ):
        revoked_remotely = False

    db.delete(connection)
    db.flush()

    return revoked_remotely