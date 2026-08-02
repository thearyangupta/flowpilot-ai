from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.oauth import GOOGLE_TOKEN_URL


class GoogleOAuthExchangeError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class GoogleTokenData:
    access_token: str = field(repr=False)
    id_token: str = field(repr=False)
    refresh_token: str | None = field(
        default=None,
        repr=False,
    )
    scopes: tuple[str, ...] = ()
    expires_at: datetime | None = None
    token_type: str = "Bearer"


def exchange_authorization_code(
    code: str,
    code_verifier: str,
    *,
    client: httpx.Client | None = None,
) -> GoogleTokenData:
    settings = get_settings()

    payload = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
    }

    owns_client = client is None
    http_client = client or httpx.Client(
        timeout=httpx.Timeout(10.0),
    )

    try:
        response = http_client.post(
            GOOGLE_TOKEN_URL,
            data=payload,
            headers={
                "Accept": "application/json",
            },
        )

        response.raise_for_status()
        response_data: dict[str, Any] = response.json()

    except (
        httpx.RequestError,
        httpx.HTTPStatusError,
        ValueError,
    ) as error:
        raise GoogleOAuthExchangeError(
            "Google authorization-code exchange failed."
        ) from error

    finally:
        if owns_client:
            http_client.close()

    access_token = response_data.get("access_token")
    id_token = response_data.get("id_token")

    if not isinstance(access_token, str) or not access_token:
        raise GoogleOAuthExchangeError(
            "Google token response did not contain an access token."
        )

    if not isinstance(id_token, str) or not id_token:
        raise GoogleOAuthExchangeError(
            "Google token response did not contain an ID token."
        )

    refresh_token = response_data.get("refresh_token")

    if refresh_token is not None and not isinstance(
        refresh_token,
        str,
    ):
        raise GoogleOAuthExchangeError(
            "Google returned an invalid refresh token."
        )

    scopes = _parse_scopes(response_data.get("scope"))
    expires_at = _calculate_expiry(
        response_data.get("expires_in")
    )

    token_type = response_data.get("token_type", "Bearer")

    if not isinstance(token_type, str):
        raise GoogleOAuthExchangeError(
            "Google returned an invalid token type."
        )

    return GoogleTokenData(
        access_token=access_token,
        id_token=id_token,
        refresh_token=refresh_token,
        scopes=scopes,
        expires_at=expires_at,
        token_type=token_type,
    )


def _parse_scopes(value: object) -> tuple[str, ...]:
    if value is None:
        return ()

    if not isinstance(value, str):
        raise GoogleOAuthExchangeError(
            "Google returned an invalid scope value."
        )

    return tuple(
        scope
        for scope in value.split()
        if scope
    )


def _calculate_expiry(
    expires_in: object,
) -> datetime | None:
    if expires_in is None:
        return None

    try:
        lifetime_seconds = int(expires_in)
    except (TypeError, ValueError) as error:
        raise GoogleOAuthExchangeError(
            "Google returned an invalid token lifetime."
        ) from error

    if lifetime_seconds <= 0:
        raise GoogleOAuthExchangeError(
            "Google returned an invalid token lifetime."
        )

    return datetime.now(timezone.utc) + timedelta(
        seconds=lifetime_seconds
    )