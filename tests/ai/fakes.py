from app.ai.schemas import EmailDecision


class FakeDecisionProvider:
    def __init__(
        self,
        decision: EmailDecision,
    ) -> None:
        self.decision = decision
        self.received_email_text: str | None = None

    def classify(
        self,
        email_text: str,
    ) -> EmailDecision:
        self.received_email_text = email_text

        return self.decision