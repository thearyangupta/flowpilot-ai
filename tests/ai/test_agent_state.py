from typing import Any

from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
)

from app.ai.agent.agent import (
    build_agent,
    invoke_agent,
)


class ConversationFakeModel(
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


def test_agent_carries_message_history_between_turns() -> None:
    model = ConversationFakeModel(
        responses=[
            AIMessage(
                content=(
                    "Order ORD-123456 "
                    "is the order we're discussing."
                ),
            ),
            AIMessage(
                content=(
                    "Yes, I remember the order "
                    "from the previous turn."
                ),
            ),
        ]
    )

    agent = build_agent(
            model=model,
            tools=[],
        )

    first_result = invoke_agent(
        agent=agent,
        message=(
            "Remember that we are discussing "
            "order ORD-123456."
        ),
    )

    first_messages = (
        first_result["messages"]
    )

    assert isinstance(
        first_messages[0],
        HumanMessage,
    )

    assert (
        first_messages[-1].content
        == (
            "Order ORD-123456 "
            "is the order we're discussing."
        )
    )

    second_result = invoke_agent(
        agent=agent,
        message=(
            "Do you remember which order "
            "we were discussing?"
        ),
        history=first_messages,
    )

    second_messages = (
        second_result["messages"]
    )

    assert len(second_messages) == 4

    assert (
        second_messages[0].content
        == (
            "Remember that we are discussing "
            "order ORD-123456."
        )
    )

    assert (
        second_messages[1].content
        == (
            "Order ORD-123456 "
            "is the order we're discussing."
        )
    )

    assert (
        second_messages[2].content
        == (
            "Do you remember which order "
            "we were discussing?"
        )
    )

    assert (
        second_messages[-1].content
        == (
            "Yes, I remember the order "
            "from the previous turn."
        )
    )