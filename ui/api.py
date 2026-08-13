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

    def google_login_url(self) -> str:
        result = self.request(
            "GET",
            "/api/v1/auth/google/start",
        )

        if not isinstance(result, dict):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        authorization_url = result.get(
            "authorization_url"
        )

        if (
            not isinstance(authorization_url, str)
            or not authorization_url
        ):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        return authorization_url

    def exchange_login_code(
        self,
        code: str,
    ) -> str:
        result = self.request(
            "POST",
            "/api/v1/auth/login-code/exchange",
            json={
                "login_code": code,
            },
        )

        if not isinstance(result, dict):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        access_token = result.get("access_token")

        if (
            not isinstance(access_token, str)
            or not access_token
        ):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        return access_token



    def get_projects(self) -> list[dict[str, Any]]:
        result = self.request(
            "GET",
            "/api/v1/projects",
        )

        if not isinstance(result, list):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        projects = []

        for project in result:
            if not isinstance(project, dict):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            project_id = project.get("id")
            name = project.get("name")

            if (
                not isinstance(project_id, str)
                or not isinstance(name, str)
            ):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            projects.append(project)

        return projects



    def create_workflow(
        self,
        *,
        project_id: str,
        name: str,
        description: str,
        template: str,
    ) -> dict[str, Any]:
        result = self.request(
            "POST",
            f"/api/v1/projects/{project_id}/workflows",
            json={
                "name": name,
                "description": description,
                "template": template,
            },
        )

        if not isinstance(result, dict):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        return result


    def list_workflows(
        self,
        *,
        project_id: str,
    ) -> list[dict[str, Any]]:
        result = self.request(
            "GET",
            f"/api/v1/projects/{project_id}/workflows",
        )

        if not isinstance(result, list):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        return result

    def close(self) -> None:
        self.http.close()


def _safe_error_message(
    response: httpx.Response,
) -> str:
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