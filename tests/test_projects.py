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


def test_create_project(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        email="project-create@example.com",
    )

    response = client.post(
        "/api/v1/projects",
        json={
            "name": "Test Project",
        },
        headers=auth_headers(user),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Project"
    assert "id" in data
    assert "created_at" in data


def test_create_project_with_empty_name_returns_422(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        email="project-empty@example.com",
    )

    response = client.post(
        "/api/v1/projects",
        json={
            "name": "   ",
        },
        headers=auth_headers(user),
    )

    assert response.status_code == 422
