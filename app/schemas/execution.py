from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, computed_field

from app.models.enums import ExecutionStatus, StepRunStatus


class ExecutionCreate(BaseModel):
    input_data: dict[str, Any]


class StepRunRead(BaseModel):
    id: UUID
    status: StepRunStatus

    started_at: datetime | None
    finished_at: datetime | None

    attempt_count: int

    error_type: str | None
    error_message: str | None

    input_data: dict[str, Any] | None
    output_data: dict[str, Any] | None

    model_config = {
        "from_attributes": True
    }

    @computed_field
    @property
    def duration_seconds(self) -> float | None:
        if self.started_at is None or self.finished_at is None:
            return None

        return (self.finished_at - self.started_at).total_seconds()

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

class ExecutionEventRead(BaseModel):
    id: UUID
    execution_id: UUID

    event_type: str

    details: dict[str, Any]

    actor: str | None
    correlation_id: str | None

    created_at: datetime

    model_config = {
        "from_attributes": True
    }