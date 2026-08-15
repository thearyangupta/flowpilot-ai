from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.base import StrictRequestModel
from app.schemas.user import UserRead


class GoogleOAuthStartRead(BaseModel):
    authorization_url: str
    expires_at: datetime


class GoogleOAuthCallbackRead(BaseModel):
    status: Literal[
        "authenticated",
        "gmail_connected",
    ]

    login_code: str | None = None
    user: UserRead


class LoginCodeExchangeCreate(
    StrictRequestModel
):
    login_code: str = Field(
        min_length=1,
        max_length=512,
    )


class AccessTokenRead(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
