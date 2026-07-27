from app.ai.providers.gemini import GeminiDecisionProvider
from app.core.config import get_settings


def test_gemini_provider_returns_email_decision():
    provider = GeminiDecisionProvider(get_settings())

    decision = provider.classify(
        """
        Hello,

        I was charged twice for my monthly subscription.
        Please refund the duplicate payment.

        Thanks.
        """
    )

    print(decision)

    assert decision.intent.value == "billing"