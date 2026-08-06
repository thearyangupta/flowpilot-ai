from typing import Any
from uuid import UUID

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.core.cipher import get_token_cipher
from app.core.config import get_settings
from app.core.oauth import (
    GOOGLE_GMAIL_SCOPES,
    GOOGLE_TOKEN_URL,
)
from app.services.auth.oauth_connection_service import (
    require_google_connection,
)
from app.services.auth.oauth_token_service import (
    get_valid_google_access_token,
)


class GoogleProviderClientError(Exception):
    pass


def build_gmail_client(
    db: Session,
    *,
    user_id: UUID,
) -> Any:
    connection = require_google_connection(
        db=db,
        user_id=user_id,
    )

    access_token = get_valid_google_access_token(
        db=db,
        connection=connection,
        cipher=get_token_cipher(),
        required_scopes=GOOGLE_GMAIL_SCOPES,
    )

    settings = get_settings()

    credentials = Credentials(
        token=access_token,
        refresh_token=None,
        token_uri=GOOGLE_TOKEN_URL,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=list(GOOGLE_GMAIL_SCOPES),
    )

    try:
        return build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )

    except Exception as error:
        raise GoogleProviderClientError(
            "Gmail client could not be constructed."
        ) from error