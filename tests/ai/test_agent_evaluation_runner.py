from typing import Any

from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import (
    AIMessage,
)

from app.ai.agent.agent import (
    build_agent,
)
from app.evaluation.agent import (
    AgentGoldenCase,
    run_agent_evaluation_case,
)


class EvaluationFakeModel(
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


def test_agent_evaluation_captures_tool_and_answer() -> None:
    model = EvaluationFakeModel(
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
                        "id": "eval-tool-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content=(
                    "Order ORD-123456 "
                    "is shipped."
                ),
            ),
        ]
    )

    agent = build_agent(
        model=model,
    )

    case = AgentGoldenCase(
        id="order-test",
        category="mcp_tool",
        input=(
            "What is the status of "
            "order ORD-123456?"
        ),
        expected_tools=(
            "lookup_order",
        ),
        expected_answer_contains=(
            "ORD-123456",
            "shipped",
        ),
        forbidden_answer_contains=(
            "delivered",
        ),
    )

    result = run_agent_evaluation_case(
        agent=agent,
        case=case,
    )

    assert result.case == case

    assert result.actual_tools == (
        "lookup_order",
    )

    assert "ORD-123456" in (
        result.final_answer
    )

    assert "shipped" in (
        result.final_answer
    )