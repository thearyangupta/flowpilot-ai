from app.core.exceptions import RetryableStepError


class FlakyHandler:
    def __init__(self, failures_before_success: int):
        self.failures_before_success = failures_before_success
        self.calls = 0

    def __call__(self, context, config):
        self.calls += 1

        if self.calls <= self.failures_before_success:
            raise RetryableStepError("Simulated timeout")

        return {"status": "ok"}


class PermanentFailureHandler:
    def __init__(self):
        self.calls = 0

    def __call__(self, context, config):
        self.calls += 1
        raise ValueError("Simulated permanent validation failure")