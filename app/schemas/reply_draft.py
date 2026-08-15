import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from app.models.enums import ReplyDraftStatus
from app.schemas.base import StrictRequestModel


class ReplyDraftRead(BaseModel):
    id: UUID
    user_id: UUID
    gmail_draft_id: str

    status: ReplyDraftStatus
    current_revision_number: int

    approved_by: UUID | None
    approved_at: datetime | None

    source_message: dict[str, Any]
    draft_message: dict[str, Any]

    gmail_message_id: str | None = None

    model_config = {
        "from_attributes": True
    }


MAX_REPLY_DRAFT_CONTENT_BYTES = 256 * 1024


class ReplyDraftDecisionCreate(
    StrictRequestModel
):
    expected_revision: int = Field(
        ge=1,
    )


class ReplyDraftRejectCreate(
    StrictRequestModel
):
    expected_revision: int = Field(
        ge=1,
    )

    reason: str = Field(
        min_length=3,
        max_length=1000,
    )


class ReplyDraftEditCreate(
    StrictRequestModel
):
    expected_revision: int = Field(
        ge=1,
    )

    content: dict[str, Any]

    @field_validator("content")
    @classmethod
    def validate_content_size(
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
                "Reply draft content must be "
                "JSON serializable."
            ) from error

        if (
            len(encoded)
            > MAX_REPLY_DRAFT_CONTENT_BYTES
        ):
            raise ValueError(
                "Reply draft content exceeds "
                "the 256 KiB limit."
            )

        return value


class ReplyDraftSendCreate(
    StrictRequestModel
):
    expected_revision: int = Field(
        ge=1,
    )


class ReplyDraftRevisionRead(BaseModel):
    id: UUID
    reply_draft_id: UUID
    user_id: UUID
    revision_number: int
    content: dict[str, Any]
    content_hash: str
    created_by_actor: str
    created_by_user_id: UUID | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ApprovalDecisionRead(BaseModel):
    id: UUID
    user_id: UUID
    revision_id: UUID
    actor_user_id: UUID | None
    action: str
    reason: str | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ReplyDraftApprovalBundleRead(BaseModel):
    draft_id: UUID
    status: ReplyDraftStatus
    current_revision_number: int
    revision: ReplyDraftRevisionRead
    decisions: list[ApprovalDecisionRead]
