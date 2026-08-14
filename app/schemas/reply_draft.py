from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import ReplyDraftStatus


class ReplyDraftRead(BaseModel):
    id: UUID
    user_id: UUID
    gmail_draft_id: str

    status: ReplyDraftStatus

    approved_by: UUID | None
    approved_at: datetime | None

    source_message: dict[str, Any]
    draft_message: dict[str, Any]

    gmail_message_id: str | None = None

    model_config = {
        "from_attributes": True
    }


class ReplyDraftRejectCreate(BaseModel):
    reason: str = Field(
        min_length=3,
        max_length=1000,
    )