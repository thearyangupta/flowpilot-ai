from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserRead


router = APIRouter()


@router.get(
    "/me",
    response_model=UserRead,
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return current_user