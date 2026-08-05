import base64
import hashlib
import secrets
from enum import StrEnum


GOOGLE_AUTHORIZATION_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth"
)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GOOGLE_REVOCATION_URL = (
    "https://oauth2.googleapis.com/revoke"
)


class OAuthPurpose(StrEnum):
    LOGIN = "login"
    GMAIL_CONNECT = "gmail_connect"


GOOGLE_IDENTITY_SCOPES: tuple[str, ...] = (
    "openid",
    "email",
    "profile",
)


GOOGLE_GMAIL_SCOPES: tuple[str, ...] = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
)


def generate_oauth_state() -> str:
    return secrets.token_urlsafe(32)


def hash_oauth_state(state: str) -> str:
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


def generate_code_verifier() -> str:
    return secrets.token_urlsafe(64)


def generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()

    challenge = base64.urlsafe_b64encode(
        digest
    ).decode("ascii")

    return challenge.rstrip("=")