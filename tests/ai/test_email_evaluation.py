import pytest

from app.ai.decision_service import DecisionService
from app.ai.schemas import EmailDecision
from tests.ai.evaluation_cases import (
    LABELLED_EMAIL_CASES,
)
from tests.ai.fakes import FakeDecisionProvider


@pytest.mark.parametrize(
    (
        "email_text",
        "expected_intent",
        "expected_urgency",
    ),
    LABELLED_EMAIL_CASES,
)
def test_labelled_email_decision(
    email_text,
    expected_intent,
    expected_urgency,
) -> None:
    expected_decision = EmailDecision(
        intent=expected_intent,
        urgency=expected_urgency,
        issue_summary="Evaluation fixture decision.",
        confidence=1.0,
        needs_human_review=False,
    )

    provider = FakeDecisionProvider(
        decision=expected_decision,
    )

    service = DecisionService(
        provider=provider,
    )

    actual_decision = service.classify(
        email_text,
    )

    assert actual_decision.intent == expected_intent
    assert actual_decision.urgency == expected_urgency
    assert provider.received_email_text == email_text