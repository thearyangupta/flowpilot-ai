from enum import Enum

from pydantic import BaseModel, Field


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