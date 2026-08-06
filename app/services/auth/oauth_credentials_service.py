from sqlalchemy.orm import Session

from app.core.cipher import TextCipher
from app.models.oauth_connection import OAuthConnection
from app.services.google.google_oauth_service import GoogleTokenData

from app.services.google.google_oauth_service import (
    GoogleRefreshedTokenData,
)


def store_google_credentials(
    db: Session,
    *,
    connection: OAuthConnection,
    token_data: GoogleTokenData,
    cipher: TextCipher,
) -> None:
    connection.access_token_ciphertext = cipher.encrypt(
        token_data.access_token
    )

    if token_data.refresh_token is not None:
        connection.refresh_token_ciphertext = cipher.encrypt(
            token_data.refresh_token
        )

    connection.scopes = list(token_data.scopes)
    connection.expires_at = token_data.expires_at

    db.flush()


def decrypt_access_token(
    connection: OAuthConnection,
    cipher: TextCipher,
) -> str:
    token = cipher.decrypt(
        connection.access_token_ciphertext
    )

    if not token:
        raise ValueError(
            "Access token is unavailable."
        )

    return token


def decrypt_refresh_token(
    connection: OAuthConnection,
    cipher: TextCipher,
) -> str:
    token = cipher.decrypt(
        connection.refresh_token_ciphertext
    )

    if not token:
        raise ValueError(
            "Refresh token is unavailable."
        )

    return token


def persist_refreshed_credentials(
    db: Session,
    *,
    connection: OAuthConnection,
    token_data: GoogleRefreshedTokenData,
    cipher: TextCipher,
) -> None:
    connection.access_token_ciphertext = (
        cipher.encrypt(
            token_data.access_token
        )
    )

    if token_data.refresh_token is not None:
        connection.refresh_token_ciphertext = (
            cipher.encrypt(
                token_data.refresh_token
            )
        )

    connection.expires_at = token_data.expires_at
    connection.scopes = list(token_data.scopes)

    db.flush()