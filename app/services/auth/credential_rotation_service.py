from sqlalchemy.orm import Session

from app.core.cipher import TokenCipher
from app.models.oauth_connection import OAuthConnection


def rotate_connection_credentials(
    db: Session,
    *,
    connection: OAuthConnection,
    cipher: TokenCipher,
) -> None:
    if connection.access_token_ciphertext is not None:
        connection.access_token_ciphertext = cipher.rotate(
            connection.access_token_ciphertext
        )

    if connection.refresh_token_ciphertext is not None:
        connection.refresh_token_ciphertext = cipher.rotate(
            connection.refresh_token_ciphertext
        )

    db.flush()