from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from app.schemas.base import StrictRequestModel


class SetValueConfig(StrictRequestModel):
    key: str = Field(
        min_length=1,
        max_length=255,
    )
    value: Any


class UppercaseConfig(StrictRequestModel):
    key: str = Field(
        min_length=1,
        max_length=255,
    )


class RequireKeyConfig(StrictRequestModel):
    key: str = Field(
        min_length=1,
        max_length=255,
    )


class SetValueStepCreate(StrictRequestModel):
    position: int = Field(
        ge=1,
        le=100,
    )
    step_type: Literal["set_value"]
    config: SetValueConfig


class UppercaseStepCreate(StrictRequestModel):
    position: int = Field(
        ge=1,
        le=100,
    )
    step_type: Literal["uppercase"]
    config: UppercaseConfig


class RequireKeyStepCreate(StrictRequestModel):
    position: int = Field(
        ge=1,
        le=100,
    )
    step_type: Literal["require_key"]
    config: RequireKeyConfig


class ClassifyEmailConfig(StrictRequestModel):
    input_key: str = Field(
        default="email_text",
        min_length=1,
        max_length=255,
    )

    output_key: str = Field(
        default="decision",
        min_length=1,
        max_length=255,
    )


class ClassifyEmailStepCreate(StrictRequestModel):
    position: int = Field(
        ge=1,
        le=100,
    )
    step_type: Literal["classify_email"]
    config: ClassifyEmailConfig


# Pydantic reads step_type and chooses
# the correct step schema.
StepCreate = Annotated[
    SetValueStepCreate
    | UppercaseStepCreate
    | RequireKeyStepCreate
    | ClassifyEmailStepCreate,
    Field(
        discriminator="step_type",
    ),
]


class WorkflowCreate(StrictRequestModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )

    steps: list[StepCreate] = Field(
        default_factory=list,
        max_length=100,
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:
        cleaned_name = value.strip()

        if not cleaned_name:
            raise ValueError(
                "Workflow name cannot be empty"
            )

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
        "from_attributes": True,
    }


class WorkflowRead(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    steps: list[WorkflowStepRead] = Field(
        default_factory=list,
    )

    model_config = {
        "from_attributes": True,
    }


class WorkflowTemplateCreate(
    StrictRequestModel
):
    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str = Field(
        default="",
        max_length=500,
    )

    template: Literal[
        "customer_reply_v1",
        "email_triage_v1",
    ]

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:
        cleaned_name = value.strip()

        if not cleaned_name:
            raise ValueError(
                "Workflow name cannot be empty"
            )

        return cleaned_name

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str,
    ) -> str:
        return value.strip()