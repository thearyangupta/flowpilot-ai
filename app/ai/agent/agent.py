from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models import (
    BaseChatModel,
)

from app.ai.agent.tools import (
    FLOWPILOT_AGENT_TOOLS,
)


AGENT_SYSTEM_PROMPT = """
You are the FlowPilot AI agent.

Help the user complete tasks using the tools
available to you.

Use tools when application data is required.

Do not invent tool results.

If no tool is needed, answer directly and
concisely.
""".strip()


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


def run_agent(
    *,
    agent,
    message: str,
) -> str:
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": message,
                }
            ]
        }
    )

    final_message = result["messages"][-1]

    return str(final_message.content)