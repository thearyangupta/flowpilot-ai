from collections.abc import Sequence
from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models import (
    BaseChatModel,
)
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
)

from app.ai.agent.tools import (
    FLOWPILOT_AGENT_TOOLS,
)
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agent.flowpilot_tools import (
    build_flowpilot_tools,
)
from app.core.config import Settings

AGENT_SYSTEM_PROMPT = """
You are the FlowPilot AI agent.

Help the user complete tasks using the tools
available to you.

Use tools when application data is required.

Do not invent tool results.

If no tool is needed, answer directly and
concisely.
""".strip()


AGENT_RECURSION_LIMIT = 12


def build_agent(
    *,
    model: BaseChatModel,
    tools: list[Any] | None = None,
):
    agent_tools = (
        FLOWPILOT_AGENT_TOOLS
        if tools is None
        else tools
    )

    return create_agent(
        model=model,
        tools=agent_tools,
        system_prompt=AGENT_SYSTEM_PROMPT,
    )

def build_flowpilot_agent(
    *,
    model: BaseChatModel,
    db: Session,
    user_id: UUID,
    settings: Settings,
):
    tools = build_flowpilot_tools(
        db=db,
        user_id=user_id,
        settings=settings,
    )

    return build_agent(
        model=model,
        tools=tools,
    )


def invoke_agent(
    *,
    agent,
    message: str,
    history: Sequence[BaseMessage] | None = None,
) -> dict[str, Any]:
    messages = list(history or [])

    messages.append(
        HumanMessage(
            content=message,
        )
    )

    return agent.invoke(
        {
            "messages": messages,
        },
        config={
            "recursion_limit":
                AGENT_RECURSION_LIMIT,
        },
    )


def run_agent(
    *,
    agent,
    message: str,
    history: Sequence[BaseMessage] | None = None,
) -> str:
    result = invoke_agent(
        agent=agent,
        message=message,
        history=history,
    )

    final_message = result["messages"][-1]

    return str(final_message.content)