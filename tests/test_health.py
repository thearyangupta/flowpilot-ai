from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "flowpilot-api",
        "environment": "development",
    }
    assert "X-Request-ID" in response.headers