from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User


class UserNotFoundError(Exception):
    pass


class InactiveUserError(Exception):
    pass


def require_active_user(
    db: Session,
    user_id: UUID,
) -> User:
    user = db.get(User, user_id)

    if user is None:
        raise UserNotFoundError

    if not user.is_active:
        raise InactiveUserError

    return user