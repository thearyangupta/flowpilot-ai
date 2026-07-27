import pytest
from pydantic import ValidationError
from app.ai.schemas import EmailDecision


def test_valid_email_decision():
    decision = EmailDecision(
        intent="billing",
        urgency="high",
        issue_summary="Customer was charged twice.",
        confidence=0.92,
        needs_human_review=False,
    )

    assert decision.intent.value == "billing"
    assert decision.urgency.value == "high"
    assert decision.confidence == 0.92


def test_invalid_intent_raises_validation_error():
    with pytest.raises(ValidationError):
        EmailDecision(
            intent="shopping",
            urgency="high",
            issue_summary="Customer wants help.",
            confidence=0.9,
            needs_human_review=False,
        )


def test_invalid_confidence_raises_validation_error():
    with pytest.raises(ValidationError):
        EmailDecision(
            intent="billing",
            urgency="high",
            issue_summary="Customer was charged twice.",
            confidence=1.4,
            needs_human_review=False,
        )


def test_short_issue_summary_raises_validation_error():
    with pytest.raises(ValidationError):
        EmailDecision(
            intent="billing",
            urgency="high",
            issue_summary="Hi",
            confidence=0.8,
            needs_human_review=False,
        )