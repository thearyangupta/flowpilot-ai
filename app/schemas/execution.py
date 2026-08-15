import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_validator,
)

from app.models.enums import (
    ExecutionStatus,
    StepRunStatus,
)
from app.schemas.base import StrictRequestModel


MAX_EXECUTION_INPUT_BYTES = 256 * 1024


class ExecutionCreate(
    StrictRequestModel
):
    input_data: dict[str, Any]

    idempotency_key: str = Field(
        min_length=1,
        max_length=255,
    )

    @field_validator("input_data")
    @classmethod
    def validate_input_data_size(
        cls,
        value: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            encoded = json.dumps(
                value,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")

        except (TypeError, ValueError) as error:
            raise ValueError(
                "Execution input must be JSON serializable."
            ) from error

        if len(encoded) > MAX_EXECUTION_INPUT_BYTES:
            raise ValueError(
                "Execution input exceeds the "
                "256 KiB limit."
            )

        return value

class WorkflowStepTraceRead(BaseModel):
    position: int
    step_type: str

    model_config = {
        "from_attributes": True
    }


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

    workflow_step: WorkflowStepTraceRead

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