from fastapi.testclient import TestClient


def test_create_project(client: TestClient) -> None:
    response = client.post(
        "/api/v1/projects",
        json={"name": "Test Project"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Project"
    assert "id" in data
    assert "created_at" in data


def test_create_project_with_empty_name_returns_422(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/projects",
        json={"name": "   "},
    )

    assert response.status_code == 422