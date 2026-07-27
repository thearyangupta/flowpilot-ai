from uuid import uuid4

from fastapi.testclient import TestClient


def test_create_workflow_with_missing_project_returns_404(
    client: TestClient,
) -> None:
    missing_project_id = uuid4()

    response = client.post(
        f"/api/v1/projects/{missing_project_id}/workflows",
        json={
            "name": "Test Workflow",
            "steps": [
                {
                    "position": 1,
                    "step_type": "set_value",
                    "config": {
                        "key": "message",
                        "value": "Hello",
                    },
                }
            ],
        },
    )

    assert response.status_code == 404