from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ReplyDraftStatus


class ReplyDraftRead(BaseModel):
    id: UUID
    user_id: UUID
    gmail_draft_id: str
    status: ReplyDraftStatus
    approved_by: UUID | None
    approved_at: datetime | None

    model_config = {
        "from_attributes": True
    }