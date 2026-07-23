from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SetValueConfig(BaseModel):
    key: str = Field(min_length=1)
    value: Any


class UppercaseConfig(BaseModel):
    key: str = Field(min_length=1)


class RequireKeyConfig(BaseModel):
    key: str = Field(min_length=1)


class SetValueStepCreate(BaseModel):
    position: int = Field(ge=1)
    step_type: Literal["set_value"]
    config: SetValueConfig


class UppercaseStepCreate(BaseModel):
    position: int = Field(ge=1)
    step_type: Literal["uppercase"]
    config: UppercaseConfig


class RequireKeyStepCreate(BaseModel):
    position: int = Field(ge=1)
    step_type: Literal["require_key"]
    config: RequireKeyConfig


# Pydantic reads step_type and chooses the correct step schema.
StepCreate = Annotated[
    SetValueStepCreate
    | UppercaseStepCreate
    | RequireKeyStepCreate,
    Field(discriminator="step_type"),
]


class WorkflowCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )
    steps: list[StepCreate] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned_name = value.strip()

        if not cleaned_name:
            raise ValueError("Workflow name cannot be empty")

        return cleaned_name


class WorkflowStepRead(BaseModel):
    id: UUID
    workflow_id: UUID
    position: int
    step_type: str
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class WorkflowRead(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    steps: list[WorkflowStepRead] = Field(default_factory=list)

    model_config = {
        "from_attributes": True
    }