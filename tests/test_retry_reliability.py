import pytest

from app.domain.retry import (
    RetryPolicy,
    execute_with_retry,
)
from tests.fault_handlers import (
    FlakyHandler,
    PermanentFailureHandler,
)
class FakeWait:
    def __init__(self):
        self.calls = []

    def __call__(self, delay: float):
        self.calls.append(delay)


def test_timeout_retries_then_succeeds():
    handler = FlakyHandler(
        failures_before_success=2,
    )

    fake_wait = FakeWait()

    policy = RetryPolicy(
        max_attempts=3,
        base_delay_seconds=1.0,
        max_delay_seconds=10.0,
    )

    result = execute_with_retry(
        operation=lambda: handler({}, {}),
        policy=policy,
        delay_function=fake_wait,
    )

    assert result == {"status": "ok"}
    assert handler.calls == 3
    assert fake_wait.calls == [1.0, 2.0]

def test_permanent_failure_is_not_retried():
    handler = PermanentFailureHandler()
    fake_wait = FakeWait()

    policy = RetryPolicy(
        max_attempts=3,
        base_delay_seconds=1.0,
        max_delay_seconds=10.0,
    )

    with pytest.raises(
        ValueError,
        match="Simulated permanent validation failure",
    ):
        execute_with_retry(
            operation=lambda: handler({}, {}),
            policy=policy,
            delay_function=fake_wait,
        )

    assert handler.calls == 1
    assert fake_wait.calls == []