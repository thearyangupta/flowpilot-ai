import httpx
import pytest

from ui.api import ApiError, FlowPilotClient, SessionExpired


def build_client(handler, token_getter=lambda: None):
    client = FlowPilotClient(
        "http://testserver",
        token_getter=token_getter,
    )

    client.http.close()
    client.http = httpx.Client(
        transport=httpx.MockTransport(handler),
        timeout=httpx.Timeout(10.0, connect=3.0),
    )

    return client


def test_request_returns_json_response():
    def handler(request):
        return httpx.Response(
            200,
            json={"ok": True},
        )

    client = build_client(handler)

    try:
        assert client.request("GET", "/test") == {"ok": True}
    finally:
        client.close()


def test_request_adds_bearer_token_when_available():
    def handler(request):
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(200, json={"ok": True})

    client = build_client(
        handler,
        token_getter=lambda: "test-token",
    )

    try:
        client.request("GET", "/test")
    finally:
        client.close()


def test_request_omits_bearer_token_when_unavailable():
    def handler(request):
        assert "Authorization" not in request.headers
        return httpx.Response(200, json={"ok": True})

    client = build_client(handler)

    try:
        client.request("GET", "/test")
    finally:
        client.close()


def test_unauthorized_response_raises_session_expired():
    def handler(request):
        return httpx.Response(
            401,
            json={"detail": "Not authenticated"},
        )

    client = build_client(handler)

    try:
        with pytest.raises(SessionExpired):
            client.request("GET", "/test")
    finally:
        client.close()


def test_network_failure_becomes_safe_api_error():
    def handler(request):
        raise httpx.ConnectError(
            "SECRET INTERNAL NETWORK DETAIL",
            request=request,
        )

    client = build_client(handler)

    try:
        with pytest.raises(ApiError) as exc_info:
            client.request("GET", "/test")

        assert exc_info.value.status == 503
        assert exc_info.value.message == "FlowPilot API is unavailable"
        assert "SECRET" not in exc_info.value.message
    finally:
        client.close()


def test_non_json_api_failure_uses_safe_fallback():
    def handler(request):
        return httpx.Response(
            500,
            text="SECRET INTERNAL SERVER DETAIL",
        )

    client = build_client(handler)

    try:
        with pytest.raises(ApiError) as exc_info:
            client.request("GET", "/test")

        assert exc_info.value.status == 500
        assert exc_info.value.message == "Request failed"
        assert "SECRET" not in exc_info.value.message
    finally:
        client.close()
