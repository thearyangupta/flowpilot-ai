from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.cipher import TextCipher
from app.core.config import get_settings
from app.core.oauth import (
    GOOGLE_AUTHORIZATION_URL,
    OAuthPurpose,
    generate_code_challenge,
    generate_code_verifier,
    generate_oauth_state,
    hash_oauth_state,
)
from app.models.oauth_attempt import OAuthAttempt


OAUTH_ATTEMPT_LIFETIME_MINUTES = 10


class OAuthStartError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class OAuthStartResult:
    authorization_url: str
    expires_at: datetime


def create_google_oauth_start(
    db: Session,
    *,
    cipher: TextCipher,
    purpose: OAuthPurpose,
    requested_scopes: tuple[str, ...],
    user_id: UUID | None = None,
    workflow_id: UUID | None = None,
) -> OAuthStartResult:
    _validate_oauth_start(
        purpose=purpose,
        requested_scopes=requested_scopes,
        user_id=user_id,
        workflow_id=workflow_id,
    )

    settings = get_settings()

    state = generate_oauth_state()
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)

    verifier_ciphertext = cipher.encrypt(verifier)

    if verifier_ciphertext is None:
        raise OAuthStartError(
            "PKCE verifier could not be encrypted."
        )

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=OAUTH_ATTEMPT_LIFETIME_MINUTES
    )

    attempt = OAuthAttempt(
        user_id=user_id,
        workflow_id=workflow_id,
        purpose=purpose.value,
        requested_scopes=list(requested_scopes),
        state_hash=hash_oauth_state(state),
        verifier_ciphertext=verifier_ciphertext,
        expires_at=expires_at,
    )

    db.add(attempt)
    db.flush()

    query_params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(requested_scopes),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "include_granted_scopes": "true",
    }

    if purpose == OAuthPurpose.GMAIL_CONNECT:
        query_params["prompt"] = "consent"

    query = urlencode(query_params)

    query = urlencode(query_params)

    return OAuthStartResult(
        authorization_url=(
            f"{GOOGLE_AUTHORIZATION_URL}?{query}"
        ),
        expires_at=expires_at,
    )


def _validate_oauth_start(
    *,
    purpose: OAuthPurpose,
    requested_scopes: tuple[str, ...],
    user_id: UUID | None,
    workflow_id: UUID | None,
) -> None:
    if not requested_scopes:
        raise OAuthStartError(
            "At least one OAuth scope is required."
        )

    if len(set(requested_scopes)) != len(requested_scopes):
        raise OAuthStartError(
            "OAuth scopes must not contain duplicates."
        )

    if (
        purpose == OAuthPurpose.LOGIN
        and user_id is not None
    ):
        raise OAuthStartError(
            "Login authorization must not be bound "
            "to an existing user."
        )

    if (
        purpose == OAuthPurpose.GMAIL_CONNECT
        and user_id is None
    ):
        raise OAuthStartError(
            "Gmail authorization requires an "
            "authenticated user."
        )

    if (
        purpose == OAuthPurpose.LOGIN
        and workflow_id is not None
    ):
        raise OAuthStartError(
            "Login authorization must not be bound "
            "to a workflow."
        )

    if (
        purpose == OAuthPurpose.GMAIL_CONNECT
        and workflow_id is None
    ):
        raise OAuthStartError(
            "Gmail authorization requires a workflow."
        )