from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.cipher import TextCipher
from app.core.config import get_settings
from app.core.oauth import (
    GOOGLE_AUTHORIZATION_URL,
    GOOGLE_IDENTITY_SCOPES,
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
) -> OAuthStartResult:
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
        state_hash=hash_oauth_state(state),
        verifier_ciphertext=verifier_ciphertext,
        expires_at=expires_at,
    )

    db.add(attempt)
    db.flush()

    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": " ".join(GOOGLE_IDENTITY_SCOPES),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "include_granted_scopes": "true",
        }
    )

    return OAuthStartResult(
        authorization_url=(
            f"{GOOGLE_AUTHORIZATION_URL}?{query}"
        ),
        expires_at=expires_at,
    )