from __future__ import annotations
from sqlalchemy import select
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.login_code import LoginCode


LOGIN_CODE_LIFETIME_MINUTES = 5

class LoginCodeNotFoundError(Exception):
    pass


class LoginCodeExpiredError(Exception):
    pass


class LoginCodeAlreadyConsumedError(Exception):
    pass



@dataclass(frozen=True, slots=True)
class LoginCodeIssueResult:
    code: str
    expires_at: datetime


def hash_login_code(code: str) -> str:
    return hashlib.sha256(
        code.encode("utf-8")
    ).hexdigest()


def issue_login_code(
    db: Session,
    *,
    user_id: UUID,
) -> LoginCodeIssueResult:
    code = secrets.token_urlsafe(32)

    expires_at = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=LOGIN_CODE_LIFETIME_MINUTES
    )

    login_code = LoginCode(
        user_id=user_id,
        code_hash=hash_login_code(code),
        expires_at=expires_at,
    )

    db.add(login_code)
    db.flush()

    return LoginCodeIssueResult(
        code=code,
        expires_at=expires_at,
    )


def consume_login_code(
    db: Session,
    *,
    code: str,
) -> LoginCode:
    code_hash = hash_login_code(code)

    statement = (
        select(LoginCode)
        .where(LoginCode.code_hash == code_hash)
        .with_for_update()
    )

    login_code = db.scalar(statement)

    if login_code is None:
        raise LoginCodeNotFoundError

    now = datetime.now(timezone.utc)

    if login_code.expires_at <= now:
        raise LoginCodeExpiredError

    if login_code.consumed_at is not None:
        raise LoginCodeAlreadyConsumedError

    login_code.consumed_at = now
    db.flush()

    return login_code