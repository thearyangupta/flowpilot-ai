from __future__ import annotations

import httpx
import pytest

from ui.api import (
    ApiError,
    FlowPilotClient,
    SessionExpired,
)


def make_client(
    handler,
    *,
    token: str | None = "test-token",
) -> FlowPilotClient:
    client = FlowPilotClient(
        "http://testserver",
        token_getter=lambda: token,
    )

    client.http.close()

    client.http = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://testserver",
    )

    return client


def test_request_adds_bearer_token() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert (
            request.headers["Authorization"]
            == "Bearer test-token"
        )

        return httpx.Response(
            200,
            json={"ok": True},
        )

    client = make_client(handler)

    try:
        result = client.request(
            "GET",
            "/api/v1/test",
        )

        assert result == {"ok": True}

    finally:
        client.close()


def test_401_becomes_session_expired() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            401,
            json={"detail": "Unauthorized"},
        )

    client = make_client(handler)

    try:
        with pytest.raises(SessionExpired):
            client.request(
                "GET",
                "/api/v1/test",
            )

    finally:
        client.close()


def test_api_failure_becomes_safe_error() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            503,
            json={
                "detail": "Service unavailable"
            },
        )

    client = make_client(handler)

    try:
        with pytest.raises(ApiError) as error:
            client.request(
                "GET",
                "/api/v1/test",
            )

        assert error.value.status == 503
        assert (
            error.value.message
            == "Service unavailable"
        )

    finally:
        client.close()


def test_pending_drafts_empty_state_data() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.url.path == (
            "/api/v1/reply-drafts"
        )

        return httpx.Response(
            200,
            json=[],
        )

    client = make_client(handler)

    try:
        result = (
            client.list_pending_reply_drafts()
        )

        assert result == []

    finally:
        client.close()


def test_pending_drafts_are_returned() -> None:
    draft_id = (
        "25b13f9b-1d7f-49e6-b55d-"
        "95b9e91f753f"
    )

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "id": draft_id,
                    "status": "pending_approval",
                    "current_revision_number": 3,
                    "gmail_draft_id": "gmail-1",
                    "source_message": {},
                    "draft_message": {},
                }
            ],
        )

    client = make_client(handler)

    try:
        result = (
            client.list_pending_reply_drafts()
        )

        assert len(result) == 1
        assert result[0]["id"] == draft_id
        assert (
            result[0]["status"]
            == "pending_approval"
        )
        assert (
            result[0]["current_revision_number"]
            == 3
        )

    finally:
        client.close()


def test_edit_sends_expected_revision_and_content() -> None:
    draft_id = (
        "25b13f9b-1d7f-49e6-b55d-"
        "95b9e91f753f"
    )

    content = {
        "recipient": "customer@example.com",
        "subject": "Updated subject",
        "body": "Updated body",
    }

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == (
            f"/api/v1/reply-drafts/"
            f"{draft_id}/revisions"
        )

        import json

        payload = json.loads(
            request.content.decode("utf-8")
        )

        assert payload == {
            "expected_revision": 3,
            "content": content,
        }

        return httpx.Response(
            200,
            json={
                "id": (
                    "4959014f-5d94-4725-a938-"
                    "563711077adb"
                ),
                "reply_draft_id": draft_id,
                "revision_number": 4,
                "content": content,
            },
        )

    client = make_client(handler)

    try:
        result = client.edit_reply_draft(
            draft_id=draft_id,
            expected_revision=3,
            content=content,
        )

        assert result["revision_number"] == 4
        assert result["content"] == content

    finally:
        client.close()


def test_approve_sends_expected_revision_and_exact_id() -> None:
    draft_id = (
        "25b13f9b-1d7f-49e6-b55d-"
        "95b9e91f753f"
    )

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == (
            f"/api/v1/reply-drafts/"
            f"{draft_id}/approve"
        )

        import json

        payload = json.loads(
            request.content.decode("utf-8")
        )

        assert payload == {
            "expected_revision": 3,
        }

        return httpx.Response(
            200,
            json={
                "id": draft_id,
                "status": "approved",
                "current_revision_number": 3,
            },
        )

    client = make_client(handler)

    try:
        result = client.approve_reply_draft(
            draft_id=draft_id,
            expected_revision=3,
        )

        assert result["id"] == draft_id
        assert result["status"] == "approved"

    finally:
        client.close()


def test_reject_sends_revision_reason_and_exact_id() -> None:
    draft_id = (
        "d6f9b0bf-7408-4317-bc89-"
        "0b294c7f090b"
    )

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == (
            f"/api/v1/reply-drafts/"
            f"{draft_id}/reject"
        )

        import json

        payload = json.loads(
            request.content.decode("utf-8")
        )

        assert payload == {
            "expected_revision": 7,
            "reason": "Incorrect answer",
        }

        return httpx.Response(
            200,
            json={
                "id": draft_id,
                "status": "rejected",
                "current_revision_number": 7,
            },
        )

    client = make_client(handler)

    try:
        result = client.reject_reply_draft(
            draft_id=draft_id,
            expected_revision=7,
            reason="Incorrect answer",
        )

        assert result["status"] == "rejected"

    finally:
        client.close()


def test_send_sends_expected_revision_and_exact_id() -> None:
    draft_id = (
        "2378fd4f-350d-48cb-b673-"
        "69b154d23d59"
    )

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == (
            f"/api/v1/reply-drafts/"
            f"{draft_id}/send"
        )

        import json

        payload = json.loads(
            request.content.decode("utf-8")
        )

        assert payload == {
            "expected_revision": 5,
        }

        return httpx.Response(
            200,
            json={
                "id": draft_id,
                "status": "sent",
                "current_revision_number": 5,
                "gmail_message_id": "gmail-message-123",
            },
        )

    client = make_client(handler)

    try:
        result = client.send_reply_draft(
            draft_id=draft_id,
            expected_revision=5,
        )

        assert result["status"] == "sent"
        assert (
            result["gmail_message_id"]
            == "gmail-message-123"
        )

    finally:
        client.close()


def test_409_preserves_safe_api_error_message() -> None:
    draft_id = (
        "c0beeb4c-9754-44cb-842f-"
        "6bf5d35ec629"
    )

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "detail": (
                    "Reply draft changed since you loaded it. "
                    "Refresh and review the latest revision "
                    "before continuing."
                )
            },
        )

    client = make_client(handler)

    try:
        with pytest.raises(ApiError) as error:
            client.approve_reply_draft(
                draft_id=draft_id,
                expected_revision=1,
            )

        assert error.value.status == 409
        assert "Refresh" in error.value.message

    finally:
        client.close()