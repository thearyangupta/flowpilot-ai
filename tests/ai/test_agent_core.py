from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel,
)

from app.ai.agent.agent import (
    build_agent,
    run_agent,
)


def test_agent_returns_final_answer() -> None:
    model = FakeListChatModel(
        responses=[
            "FlowPilot agent is ready.",
        ],
    )

    agent = build_agent(
        model=model,
        tools=[],
    )

    result = run_agent(
        agent=agent,
        message="Are you ready?",
    )

    assert result == (
        "FlowPilot agent is ready."
    )