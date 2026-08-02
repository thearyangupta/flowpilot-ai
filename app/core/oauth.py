import base64
import hashlib
import secrets


GOOGLE_IDENTITY_SCOPES: tuple[str, ...] = (
    "openid",
    "email",
    "profile",
)


def generate_oauth_state() -> str:
    return secrets.token_urlsafe(32)


def hash_oauth_state(state: str) -> str:
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


def generate_code_verifier() -> str:
    return secrets.token_urlsafe(64)


def generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()

    challenge = base64.urlsafe_b64encode(digest).decode("ascii")

    return challenge.rstrip("=")