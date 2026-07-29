import time
from collections.abc import Callable
from typing import TypeVar

from app.core.exceptions import RetryableStepError
from dataclasses import dataclass


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0

def calculate_backoff_delay(
    attempt_number: int,
    policy: RetryPolicy,
) -> float:
    delay = policy.base_delay_seconds * (2 ** (attempt_number - 1))

    return min(delay, policy.max_delay_seconds)

T = TypeVar("T")


def execute_with_retry(
    operation: Callable[[], T],
    policy: RetryPolicy,
    delay_function: Callable[[float], None] = time.sleep,
) -> T:
    attempt_number = 0

    while attempt_number < policy.max_attempts:
        attempt_number += 1

        try:
            return operation()

        except RetryableStepError:
            if attempt_number >= policy.max_attempts:
                raise

            delay = calculate_backoff_delay(
                attempt_number=attempt_number,
                policy=policy,
            )

            delay_function(delay)

    raise RuntimeError("Retry execution ended unexpectedly")