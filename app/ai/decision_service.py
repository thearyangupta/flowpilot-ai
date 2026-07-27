from app.ai.schemas import EmailDecision,Intent,Urgency
from app.ai.providers.gemini import GeminiDecisionProvider
from app.ai.exceptions import AIProviderError

MIN_CONFIDENCE = 0.75

class DecisionService:
    def __init__(self, provider: GeminiDecisionProvider):
        self._provider = provider

    def classify(self, email: str) -> EmailDecision:
        try:
            decision = self._provider.classify(email)

            if decision.confidence < MIN_CONFIDENCE:
                decision.needs_human_review = True

            return decision

        except AIProviderError:
            return EmailDecision(
                intent=Intent.other,
                urgency=Urgency.medium,
                issue_summary="AI classification unavailable; human review required.",
                confidence=0.0,
                needs_human_review=True,
        )