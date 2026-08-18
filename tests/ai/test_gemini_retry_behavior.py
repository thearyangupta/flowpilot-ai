from google.genai import errors
import pytest

from app.ai.providers.gemini import (
    _raise_gemini_provider_error,
)
from app.core.exceptions import (
    RetryableStepError,
)


def test_transient_gemini_error_is_retryable():
    error = errors.ServerError(
        503,
        {
            "error": {
                "code": 503,
                "message": "temporarily unavailable",
            }
        },
        None,
    )

    with pytest.raises(
        RetryableStepError
    ):
        _raise_gemini_provider_error(
            error,
            message="temporary failure",
        )


def test_non_api_error_is_not_retryable():
    with pytest.raises(Exception) as exc_info:
        _raise_gemini_provider_error(
            ValueError("bad input"),
            message="provider failure",
        )

    assert (
        type(exc_info.value).__name__
        == "AIProviderError"
    )