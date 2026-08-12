from enum import Enum

from pydantic import BaseModel, Field,ConfigDict


class Intent(str, Enum):
    billing = "billing"
    technical = "technical"
    account = "account"
    feedback = "feedback"
    other = "other"


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class EmailDecision(BaseModel):
    intent: Intent = Field(
        description="Classified customer support intent."
    )

    urgency: Urgency = Field(
        description="Estimated urgency level of the customer's issue."
    )

    issue_summary: str = Field(
        min_length=5,
        max_length=300,
        description="Short factual summary of the customer's issue."
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Model confidence score between 0.0 and 1.0."
    )

    needs_human_review: bool = Field(
        description="Whether the decision should be reviewed by a human before workflow execution."
    )


class EmailDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str = Field(
        min_length=1,
        max_length=998,
        description="Draft email subject.",
    )

    body: str = Field(
        min_length=1,
        max_length=5000,
        description="Draft email body.",
    )


class GroundedReply(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str = Field(
        min_length=1,
        max_length=998,
        description="Grounded reply subject.",
    )

    body: str = Field(
        min_length=1,
        max_length=5000,
        description="Grounded reply body with source citations.",
    )

    citation_ids: list[str] = Field(
        default_factory=list,
        description="Knowledge source labels used by the reply.",
    )

    unsupported: bool = Field(
        description=(
            "True when the supplied knowledge does not "
            "adequately support a safe reply."
        ),
    )

    missing_information: list[str] = Field(
        default_factory=list,
        description=(
            "Information required to answer safely "
            "when evidence is insufficient."
        ),
    )