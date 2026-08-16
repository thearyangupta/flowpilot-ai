from typing import Any

from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import AIMessage

from app.ai.agent.agent import build_agent


class ToolCallingFakeModel(
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


def test_agent_executes_tool_and_observes_result() -> None:
    model = ToolCallingFakeModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "lookup_order",
                        "args": {
                            "order_id":
                                "ORD-123456",
                        },
                        "id": "call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content=(
                    "Order ORD-123456 "
                    "has been shipped."
                ),
            ),
        ]
    )

    agent = build_agent(
        model=model,
    )

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "What is the status of "
                        "order ORD-123456?"
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

    assert "shipped" in str(
        tool_messages[0].content
    )

    assert (
        messages[-1].content
        == "Order ORD-123456 has been shipped."
    )