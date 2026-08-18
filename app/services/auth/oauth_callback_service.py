from dataclasses import dataclass
from uuid import UUID
import logging
from sqlalchemy.orm import Session

from app.core.cipher import TextCipher
from app.core.oauth import (
    GOOGLE_GMAIL_SCOPES,
    OAuthPurpose,
    hash_oauth_state,
)
from app.services.auth.login_code_service import issue_login_code
from app.models.user import User
from app.services.google.google_identity_service import (
    GoogleIdentity,
    GoogleIdentityVerificationError,
    verify_google_id_token,
)
from app.services.google.google_oauth_service import (
    GoogleOAuthExchangeError,
    GoogleTokenData,
    exchange_authorization_code,
)
from app.services.auth.oauth_attempt_service import (
    OAuthAttemptAlreadyConsumedError,
    OAuthAttemptExpiredError,
    OAuthAttemptNotFoundError,
    OAuthVerifierUnavailableError,
    consume_oauth_attempt,
    decrypt_attempt_verifier,
)
from app.services.auth.oauth_connection_service import (
    GoogleConnectionNotFoundError,
    GoogleIdentityMismatchError,
    ensure_google_identity_matches,
    require_google_connection,
)
from app.services.auth.oauth_credentials_service import (
    store_google_credentials,
)
from app.services.auth.oauth_identity_service import (
    resolve_google_identity,
)
from app.services.auth.oauth_token_service import (
    MissingGoogleScopes,
    ensure_granted_google_scopes,
)
from app.services.google.gmail_cursor_service import (
    save_gmail_history_cursor,
)
from app.services.google.gmail_poll_service import (
    get_gmail_history_cursor,
)

logger = logging.getLogger(__name__)

class OAuthCallbackError(Exception):
    pass


class UnsupportedOAuthPurposeError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class OAuthCallbackResult:
    purpose: OAuthPurpose
    user: User
    google_token_data: GoogleTokenData
    login_code: str | None = None


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

        try:
            purpose = OAuthPurpose(attempt.purpose)
        except ValueError as error:
            raise UnsupportedOAuthPurposeError(
                "OAuth attempt has an unsupported purpose."
            ) from error

        if purpose == OAuthPurpose.LOGIN:
            return _complete_login_callback(
                db=db,
                identity=google_identity,
                token_data=google_token_data,
                cipher=cipher,
            )

        if purpose == OAuthPurpose.GMAIL_CONNECT:
            if attempt.user_id is None:
                raise OAuthCallbackError(
                    "Gmail authorization attempt has no user."
                )

            ensure_granted_google_scopes(
                granted_scopes=google_token_data.scopes,
                required_scopes=GOOGLE_GMAIL_SCOPES,
            )

            return _complete_gmail_connect_callback(
                db=db,
                user_id=attempt.user_id,
                identity=google_identity,
                token_data=google_token_data,
                cipher=cipher,
            )

        raise UnsupportedOAuthPurposeError(
            "OAuth attempt has an unsupported purpose."
        )

    except (
        OAuthAttemptNotFoundError,
        OAuthAttemptExpiredError,
        OAuthAttemptAlreadyConsumedError,
        OAuthVerifierUnavailableError,
        GoogleOAuthExchangeError,
        GoogleIdentityVerificationError,
        MissingGoogleScopes,
        GoogleConnectionNotFoundError,
        GoogleIdentityMismatchError,
        UnsupportedOAuthPurposeError,
    ) as error:
        logger.exception(
            "Google 0Auth callback failed: %s",
            type(error).__name__,
        )
        raise OAuthCallbackError(
            "Google OAuth callback could not be completed."
        ) from error


def _complete_login_callback(
    db: Session,
    *,
    identity: GoogleIdentity,
    token_data: GoogleTokenData,
    cipher: TextCipher,
) -> OAuthCallbackResult:
    user = resolve_google_identity(
        db=db,
        identity=identity,
    )

    login_code = issue_login_code(
        db,
        user_id=user.id,
    )

    return OAuthCallbackResult(
        purpose=OAuthPurpose.LOGIN,
        user=user,
        google_token_data=token_data,
        login_code=login_code.code,
    )


def _complete_gmail_connect_callback(
    db: Session,
    *,
    user_id: UUID,
    identity: GoogleIdentity,
    token_data: GoogleTokenData,
    cipher: TextCipher,
) -> OAuthCallbackResult:
    connection = require_google_connection(
        db=db,
        user_id=user_id,
    )

    ensure_google_identity_matches(
        connection,
        provider_subject=identity.subject,
    )

    user = connection.user
    user.email = identity.email
    user.display_name = identity.display_name

    store_google_credentials(
        db=db,
        connection=connection,
        token_data=token_data,
        cipher=cipher,
    )

    db.flush()

    history_id = get_gmail_history_cursor(
        db=db,
        user_id=user_id,
    )

    save_gmail_history_cursor(
        db=db,
        connection=connection,
        history_id=history_id,
    )

    db.flush()

    return OAuthCallbackResult(
        purpose=OAuthPurpose.GMAIL_CONNECT,
        user=user,
        google_token_data=token_data,
    )