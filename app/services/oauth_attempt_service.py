from datetime import datetime, timezone
from app.core.cipher import TextCipher
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.oauth_attempt import OAuthAttempt


class OAuthAttemptNotFoundError(Exception):
    pass


class OAuthAttemptExpiredError(Exception):
    pass


class OAuthAttemptAlreadyConsumedError(Exception):
    pass


class OAuthVerifierUnavailableError(Exception):
    pass


def consume_oauth_attempt(
    db: Session,
    state_hash: str,
) -> OAuthAttempt:
    statement = (
        select(OAuthAttempt)
        .where(OAuthAttempt.state_hash == state_hash)
        .with_for_update()
    )

    attempt = db.scalar(statement)

    if attempt is None:
        raise OAuthAttemptNotFoundError

    now = datetime.now(timezone.utc)

    if attempt.expires_at <= now:
        raise OAuthAttemptExpiredError

    if attempt.consumed_at is not None:
        raise OAuthAttemptAlreadyConsumedError

    attempt.consumed_at = now
    db.flush()

    return attempt


def decrypt_attempt_verifier(
    attempt: OAuthAttempt,
    cipher: TextCipher,
) -> str:
    verifier = cipher.decrypt(
        attempt.verifier_ciphertext
    )

    if not verifier:
        raise OAuthVerifierUnavailableError

    return verifier