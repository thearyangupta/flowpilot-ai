from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ExecutionStatus, StepRunStatus


class ExecutionCreate(BaseModel):
    input_data: dict[str, Any]


class StepRunRead(BaseModel):
    id: UUID
    status: StepRunStatus
    input_data: dict[str, Any] | None
    output_data: dict[str, Any] | None
    error: str | None

    model_config = {
        "from_attributes": True
    }

class ExecutionRead(BaseModel):
    id: UUID
    workflow_id: UUID
    status: ExecutionStatus
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class ExecutionDetail(BaseModel):
    id: UUID
    workflow_id: UUID
    status: ExecutionStatus
    created_at: datetime
    updated_at: datetime
    step_runs: list[StepRunRead]

    model_config = {
        "from_attributes": True
    }