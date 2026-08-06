from dataclasses import dataclass

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config import get_settings


class GoogleIdentityVerificationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class GoogleIdentity:
    subject: str
    email: str
    display_name: str | None = None


def verify_google_id_token(
    raw_id_token: str,
) -> GoogleIdentity:
    settings = get_settings()

    try:
        claims = id_token.verify_oauth2_token(
            raw_id_token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except Exception as error:
        raise GoogleIdentityVerificationError(
            "Google ID-token verification failed."
        ) from error

    subject = claims.get("sub")
    email = claims.get("email")
    email_verified = claims.get("email_verified")
    display_name = claims.get("name")

    if not isinstance(subject, str) or not subject:
        raise GoogleIdentityVerificationError(
            "Google ID token did not contain a valid subject."
        )

    if not isinstance(email, str) or not email:
        raise GoogleIdentityVerificationError(
            "Google ID token did not contain a valid email."
        )

    if email_verified is not True:
        raise GoogleIdentityVerificationError(
            "Google email is not verified."
        )

    if display_name is not None and not isinstance(
        display_name,
        str,
    ):
        raise GoogleIdentityVerificationError(
            "Google ID token contained an invalid display name."
        )

    return GoogleIdentity(
        subject=subject,
        email=email,
        display_name=display_name,
    )