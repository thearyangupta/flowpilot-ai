from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User


def create_user(
    db_session: Session,
    *,
    email: str,
) -> User:
    user = User(
        email=email,
        display_name=email,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def auth_headers(
    user: User,
) -> dict[str, str]:
    return {
        "Authorization":
            f"Bearer {create_access_token(user.id)}",
    }


def test_create_workflow_with_missing_project_returns_404(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        email="workflow-missing@example.com",
    )

    missing_project_id = uuid4()

    response = client.post(
        f"/api/v1/projects/"
        f"{missing_project_id}/workflows",
        json={
            "name": "Test Workflow",
            "description":
                "Missing project test",
            "template":
                "customer_reply_v1",
        },
        headers=auth_headers(user),
    )

    assert response.status_code == 404
