from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import httpx


DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"

TokenGetter = Callable[[], str | None]


class ApiError(Exception):
    """Safe API error that may be presented by the UI."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class SessionExpired(Exception):
    """Raised when the API rejects the current authentication session."""


class FlowPilotClient:
    """Thin HTTP client for the FlowPilot FastAPI application."""

    def __init__(
        self,
        base_url: str,
        token_getter: TokenGetter | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token_getter = token_getter or (lambda: None)

        self.http = httpx.Client(
            timeout=httpx.Timeout(
                timeout=10.0,
                connect=3.0,
            )
        )

    def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        headers = dict(kwargs.pop("headers", {}))

        token = self.token_getter()

        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = self.http.request(
                method=method,
                url=f"{self.base_url}{path}",
                headers=headers,
                **kwargs,
            )
        except httpx.RequestError as exc:
            raise ApiError(
                503,
                "FlowPilot API is unavailable",
            ) from exc

        if response.status_code == 401:
            raise SessionExpired()

        if response.is_error:
            raise ApiError(
                response.status_code,
                _safe_error_message(response),
            )

        if not response.content:
            return None

        return response.json()

    def close(self) -> None:
        self.http.close()


def _safe_error_message(response: httpx.Response) -> str:
    """Extract a user-safe error message from a FastAPI response."""

    try:
        payload = response.json()
    except ValueError:
        return "Request failed"

    if not isinstance(payload, dict):
        return "Request failed"

    detail = payload.get("detail")

    if isinstance(detail, str) and detail.strip():
        return detail

    return "Request failed"


def get_api_base_url() -> str:
    """Return the FlowPilot API base URL from environment configuration."""

    return os.getenv(
        "FLOWPILOT_API_BASE_URL",
        DEFAULT_API_BASE_URL,
    )