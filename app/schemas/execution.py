from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ExecutionStatus


class ExecutionCreate(BaseModel):
    pass


class ExecutionRead(BaseModel):
    id: UUID
    workflow_id: UUID
    status: ExecutionStatus
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }