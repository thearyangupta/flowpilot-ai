from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import httpx


DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"

DEFAULT_BROWSER_API_BASE_URL = (
    "http://localhost:8000"
)

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



    def gmail_connect_url(
        self,
        workflow_id: str,
    ) -> str:
        result = self.request(
            "GET",
            "/api/v1/integrations/gmail/connect",
            params={
                "workflow_id": workflow_id,
            },
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


    def chat_with_agent(
        self,
        message: str,
    ) -> str:
        result = self.request(
            "POST",
            "/api/v1/agent/chat",
            json={
                "message": message,
            },
            timeout=330.0,
        )

        if not isinstance(result, dict):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        response_message = result.get(
            "message"
        )

        if (
            not isinstance(
                response_message,
                str,
            )
            or not response_message
        ):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        return response_message

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

    def create_project(
        self,
        *,
        name: str,
    ) -> dict[str, Any]:
        result = self.request(
            "POST",
            "/api/v1/projects",
            json={
                "name": name,
            },
        )

        if not isinstance(result, dict):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        project_id = result.get("id")
        project_name = result.get("name")

        if (
            not isinstance(project_id, str)
            or not isinstance(project_name, str)
        ):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        return result



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



    def upload_knowledge_document(
        self,
    *   ,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict[str, Any]:
        result = self.request(
            "POST",
            "/api/v1/knowledge/documents",
            files={
                "file": (
                    filename,
                    content,
                    content_type,
                ),
            },
        )

        if not isinstance(result, dict):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        document_id = result.get("id")
        name = result.get("name")
        document_status = result.get("status")

        if (
            not isinstance(document_id, str)
            or not isinstance(name, str)
            or not isinstance(document_status, str)
        ):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        return result
    def list_knowledge_documents(
        self,
    ) -> list[dict[str, Any]]:
        result = self.request(
            "GET",
            "/api/v1/knowledge/documents",
        )

        if not isinstance(result, list):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        documents: list[dict[str, Any]] = []

        for document in result:
            if not isinstance(document, dict):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            if not isinstance(document.get("id"), str):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            if not isinstance(document.get("name"), str):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            if not isinstance(document.get("status"), str):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            documents.append(document)

        return documents


    def get_knowledge_document(
        self,
        *,
        document_id: str,
    ) -> dict[str, Any]:
        result = self.request(
            "GET",
            f"/api/v1/knowledge/documents/{document_id}",
        )

        if not isinstance(result, dict):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        if not isinstance(result.get("id"), str):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        if not isinstance(result.get("name"), str):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        if not isinstance(result.get("status"), str):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        return result

    def list_executions(
        self,
        *,
        project_id: str,
        workflow_id: str,
        execution_status: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}

        if execution_status:
            params["execution_status"] = execution_status

        result = self.request(
            "GET",
            (
                f"/api/v1/projects/{project_id}"
                f"/workflows/{workflow_id}/executions"
            ),
            params=params,
        )

        if not isinstance(result, list):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        executions: list[dict[str, Any]] = []

        for execution in result:
            if not isinstance(execution, dict):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            if not isinstance(execution.get("id"), str):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            if not isinstance(
                execution.get("workflow_id"),
                str,
            ):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            if not isinstance(
                execution.get("status"),
                str,
            ):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            executions.append(execution)

        return executions


    def get_execution_detail(
        self,
        *,
        execution_id: str,
    ) -> dict[str, Any]:
        result = self.request(
            "GET",
            f"/api/v1/executions/{execution_id}",
        )

        if not isinstance(result, dict):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        if not isinstance(result.get("id"), str):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        step_runs = result.get("step_runs")

        if not isinstance(step_runs, list):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        return result


    def list_pending_reply_drafts(
        self,
    ) -> list[dict[str, Any]]:
        result = self.request(
            "GET",
            "/api/v1/reply-drafts",
        )

        if not isinstance(result, list):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        drafts: list[dict[str, Any]] = []

        for draft in result:
            if not isinstance(draft, dict):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            if not isinstance(
                draft.get("id"),
                str,
            ):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            if not isinstance(
                draft.get("status"),
                str,
            ):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            if not isinstance(
                draft.get("current_revision_number"),
                int,
            ):
                raise ApiError(
                    502,
                    "FlowPilot API returned an invalid response",
                )

            drafts.append(draft)

        return drafts


    def edit_reply_draft(
        self,
        *,
        draft_id: str,
        expected_revision: int,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        result = self.request(
            "POST",
            (
                f"/api/v1/reply-drafts/"
                f"{draft_id}/revisions"
            ),
            json={
                "expected_revision": expected_revision,
                "content": content,
            },
        )

        if not isinstance(result, dict):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        return result


    def approve_reply_draft(
        self,
        *,
        draft_id: str,
        expected_revision: int,
    ) -> dict[str, Any]:
        result = self.request(
            "POST",
            (
                f"/api/v1/reply-drafts/"
                f"{draft_id}/approve"
            ),
            json={
                "expected_revision": expected_revision,
            },
        )

        if not isinstance(result, dict):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        return result


    def reject_reply_draft(
        self,
        *,
        draft_id: str,
        expected_revision: int,
        reason: str,
    ) -> dict[str, Any]:
        result = self.request(
            "POST",
            (
                f"/api/v1/reply-drafts/"
                f"{draft_id}/reject"
            ),
            json={
                "expected_revision": expected_revision,
                "reason": reason,
            },
        )

        if not isinstance(result, dict):
            raise ApiError(
                502,
                "FlowPilot API returned an invalid response",
            )

        return result


    def send_reply_draft(
        self,
        *,
        draft_id: str,
        expected_revision: int,
    ) -> dict[str, Any]:
        idempotency_key = (
            f"reply-draft:{draft_id}:"
            f"revision:{expected_revision}:send"
        )

        result = self.request(
            "POST",
            (
                f"/api/v1/reply-drafts/"
                f"{draft_id}/send"
            ),
            json={
                "expected_revision":
                    expected_revision,
                "idempotency_key":
                    idempotency_key,
            },
        )

        if not isinstance(result, dict):
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

def get_browser_api_base_url() -> str:
    return os.getenv(
        "FLOWPILOT_BROWSER_API_BASE_URL",
        DEFAULT_BROWSER_API_BASE_URL,
    ).rstrip("/")


def get_api_base_url() -> str:
    """Return the FlowPilot API base URL from environment configuration."""

    return os.getenv(
        "FLOWPILOT_API_BASE_URL",
        DEFAULT_API_BASE_URL,
    )