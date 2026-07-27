from app.ai.decision_service import DecisionService
from app.ai.schemas import EmailDecision, Intent, Urgency
from app.ai.exceptions import AIProviderError

class FakeProvider:
    def classify(self, email: str) -> EmailDecision:
        return EmailDecision(
            intent=Intent.billing,
            urgency=Urgency.medium,
            issue_summary="Customer was charged twice.",
            confidence=0.50,
            needs_human_review=False,
        )


def test_low_confidence_requires_human_review():
    service = DecisionService(FakeProvider())

    decision = service.classify("I was charged twice.")

    assert decision.needs_human_review is True


class FailingProvider:
    def classify(self, email: str):
        raise AIProviderError("Gemini unavailable")


def test_provider_failure_returns_safe_fallback():
    service = DecisionService(FailingProvider())

    decision = service.classify("Hello")

    assert decision.intent == Intent.other
    assert decision.urgency == Urgency.medium
    assert decision.confidence == 0.0
    assert decision.needs_human_review is True