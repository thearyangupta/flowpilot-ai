from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.cipher import TextCipher
from app.models.oauth_connection import OAuthConnection
from app.services.google.google_oauth_service import (
    refresh_google_access_token,
)
from app.services.auth.oauth_credentials_service import (
    decrypt_access_token,
    decrypt_refresh_token,
    persist_refreshed_credentials,
)


EXPIRY_SAFETY_WINDOW = timedelta(minutes=2)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def should_refresh(
    connection: OAuthConnection,
) -> bool:
    expires_at = connection.expires_at

    if expires_at is None:
        return True

    return expires_at <= (
        utc_now() + EXPIRY_SAFETY_WINDOW
    )


class MissingGoogleScopes(Exception):
    def __init__(
        self,
        required_scopes: set[str],
        granted_scopes: set[str],
    ) -> None:
        self.required_scopes = required_scopes
        self.granted_scopes = granted_scopes
        self.missing_scopes = (
            required_scopes - granted_scopes
        )

        missing = ", ".join(
            sorted(self.missing_scopes)
        )

        super().__init__(
            f"Missing required Google scopes: {missing}"
        )


def ensure_granted_google_scopes(
    *,
    granted_scopes: Iterable[str],
    required_scopes: Iterable[str],
) -> None:
    required = set(required_scopes)
    granted = set(granted_scopes)

    if not required.issubset(granted):
        raise MissingGoogleScopes(
            required_scopes=required,
            granted_scopes=granted,
        )


def ensure_google_scopes(
    connection: OAuthConnection,
    required_scopes: Iterable[str],
) -> None:
    ensure_granted_google_scopes(
        granted_scopes=connection.scopes or [],
        required_scopes=required_scopes,
    )


def get_valid_google_access_token(
    db: Session,
    *,
    connection: OAuthConnection,
    cipher: TextCipher,
    required_scopes: Iterable[str],
) -> str:
    ensure_google_scopes(
        connection,
        required_scopes,
    )

    if should_refresh(connection):
        refresh_token = decrypt_refresh_token(
            connection,
            cipher,
        )

        refreshed = refresh_google_access_token(
            refresh_token
        )

        persist_refreshed_credentials(
            db=db,
            connection=connection,
            token_data=refreshed,
            cipher=cipher,
        )

    return decrypt_access_token(
        connection,
        cipher,
    )