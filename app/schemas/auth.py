from datetime import datetime

from pydantic import BaseModel

from app.schemas.user import UserRead


class GoogleOAuthStartRead(BaseModel):
    authorization_url: str
    expires_at: datetime


class GoogleOAuthCallbackRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead