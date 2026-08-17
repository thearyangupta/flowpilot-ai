from typing import Any
from types import SimpleNamespace
from uuid import uuid4

from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import (
    AIMessage,
)

from app.ai.agent.agent import (
    build_flowpilot_agent,
)


class FlowPilotToolCallingFakeModel(
    FakeMessagesListChatModel,
):
    def bind_tools(
        self,
        tools: Any,
        *,
        tool_choice: Any = None,
        **kwargs: Any,
    ):
        return self


def test_agent_uses_real_flowpilot_project_tool(
    monkeypatch,
) -> None:
    user_id = uuid4()

    project = SimpleNamespace(
        id=uuid4(),
        name="Recruiter Demo",
    )

    captured = {}

    def fake_get_all(
        db,
        user_id,
    ):
        captured["db"] = db
        captured["user_id"] = user_id

        return [project]

    monkeypatch.setattr(
        "app.ai.agent.flowpilot_tools."
        "project_service.get_all",
        fake_get_all,
    )

    model = FlowPilotToolCallingFakeModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "list_projects",
                        "args": {},
                        "id": "call-projects-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content=(
                    "You have a project named "
                    "Recruiter Demo."
                ),
            ),
        ]
    )

    fake_db = object()
    fake_settings = object()

    agent = build_flowpilot_agent(
        model=model,
        db=fake_db,
        user_id=user_id,
        settings=fake_settings,
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "What FlowPilot projects "
                        "do I have?"
                    ),
                }
            ]
        }
    )

    messages = result["messages"]

    tool_messages = [
        message
        for message in messages
        if message.type == "tool"
    ]

    assert len(tool_messages) == 1

    assert (
        tool_messages[0].name
        == "list_projects"
    )

    assert "Recruiter Demo" in str(
        tool_messages[0].content
    )

    assert captured["db"] is fake_db
    assert captured["user_id"] == user_id

    assert (
        messages[-1].content
        == (
            "You have a project named "
            "Recruiter Demo."
        )
    )