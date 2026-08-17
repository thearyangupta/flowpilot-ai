from typing import Any

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from sqlalchemy.orm import Session

from app.api.routers import agent as agent_router
from app.core.security import create_access_token
from app.models.user import User


def create_user(
    db_session: Session,
) -> User:
    user = User(
        email="agent-api@example.com",
        display_name="Agent API User",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


class FakeAgent:
    def __init__(self) -> None:
        self.received_input: dict[str, Any] | None = None

    def invoke(
        self,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        self.received_input = input_data

        return {
            "messages": [
                AIMessage(
                    content=(
                        "You have a project named "
                        "Recruiter Demo."
                    ),
                )
            ]
        }


def test_agent_chat_uses_authenticated_user(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    user = create_user(
        db_session,
    )

    fake_agent = FakeAgent()

    captured: dict[str, Any] = {}

    fake_model = object()

    def fake_build_agent_model(
        settings,
    ):
        captured["model_settings"] = settings

        return fake_model

    def fake_build_flowpilot_agent(
        *,
        model,
        db,
        user_id,
        settings,
    ):
        captured["model"] = model
        captured["db"] = db
        captured["user_id"] = user_id
        captured["settings"] = settings

        return fake_agent

    monkeypatch.setattr(
        agent_router,
        "build_agent_model",
        fake_build_agent_model,
    )

    monkeypatch.setattr(
        agent_router,
        "build_flowpilot_agent",
        fake_build_flowpilot_agent,
    )

    response = client.post(
        "/api/v1/agent/chat",
        json={
            "message":
                "What FlowPilot projects do I have?",
        },
        headers={
            "Authorization": (
                f"Bearer "
                f"{create_access_token(user.id)}"
            ),
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": (
            "You have a project named "
            "Recruiter Demo."
        )
    }

    assert captured["user_id"] == user.id
    assert captured["model"] is fake_model
    assert captured["db"] is db_session

    assert (
        fake_agent.received_input
        is not None
    )

    messages = (
        fake_agent.received_input[
            "messages"
        ]
    )

    assert messages == [
        {
            "role": "user",
            "content":
                "What FlowPilot projects do I have?",
        }
    ]