from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.user import UserRead


class GoogleOAuthStartRead(BaseModel):
    authorization_url: str
    expires_at: datetime


class GoogleOAuthCallbackRead(BaseModel):
    status: Literal[
        "authenticated",
        "gmail_connected",
    ]

    access_token: str | None = None
    token_type: str | None = None
    user: UserRead