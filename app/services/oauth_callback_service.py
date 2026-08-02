from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.cipher import TextCipher
from app.core.oauth import hash_oauth_state
from app.core.security import create_access_token
from app.models.user import User
from app.services.google_identity_service import (
    GoogleIdentityVerificationError,
    verify_google_id_token,
)
from app.services.google_oauth_service import (
    GoogleOAuthExchangeError,
    GoogleTokenData,
    exchange_authorization_code,
)
from app.services.oauth_attempt_service import (
    OAuthAttemptAlreadyConsumedError,
    OAuthAttemptExpiredError,
    OAuthAttemptNotFoundError,
    OAuthVerifierUnavailableError,
    consume_oauth_attempt,
    decrypt_attempt_verifier,
)
from app.services.oauth_identity_service import (
    resolve_google_identity,
)


class OAuthCallbackError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class OAuthCallbackResult:
    user: User
    flowpilot_access_token: str
    google_token_data: GoogleTokenData


def complete_google_oauth_callback(
    db: Session,
    *,
    code: str,
    state: str,
    cipher: TextCipher,
) -> OAuthCallbackResult:
    try:
        state_hash = hash_oauth_state(state)

        attempt = consume_oauth_attempt(
            db=db,
            state_hash=state_hash,
        )

        code_verifier = decrypt_attempt_verifier(
            attempt=attempt,
            cipher=cipher,
        )

        google_token_data = exchange_authorization_code(
            code=code,
            code_verifier=code_verifier,
        )

        google_identity = verify_google_id_token(
            google_token_data.id_token
        )

        user = resolve_google_identity(
            db=db,
            identity=google_identity,
        )

        flowpilot_access_token = create_access_token(
            user.id
        )

        return OAuthCallbackResult(
            user=user,
            flowpilot_access_token=flowpilot_access_token,
            google_token_data=google_token_data,
        )

    except (
        OAuthAttemptNotFoundError,
        OAuthAttemptExpiredError,
        OAuthAttemptAlreadyConsumedError,
        OAuthVerifierUnavailableError,
        GoogleOAuthExchangeError,
        GoogleIdentityVerificationError,
    ) as error:
        raise OAuthCallbackError(
            "Google OAuth callback could not be completed."
        ) from error