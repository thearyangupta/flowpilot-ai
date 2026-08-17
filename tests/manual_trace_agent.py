from dotenv import load_dotenv

load_dotenv(
    override=True,
)
from langchain_core.tracers.langchain import (
    wait_for_all_tracers,
)

from app.ai.agent.agent import (
    build_agent,
    invoke_agent,
)
from app.ai.agent.model import (
    build_agent_model,
)
from app.core.config import get_settings


def main() -> None:
    settings = get_settings()

    model = build_agent_model(
        settings,
    )

    agent = build_agent(
        model=model,
    )

    try:
        result = invoke_agent(
            agent=agent,
            message=(
                "What is the status of "
                "order ORD-123456?"
            ),
        )

        final_message = (
            result["messages"][-1]
        )

        print(
            "AGENT_RESPONSE =",
            final_message.content,
        )

    finally:
        wait_for_all_tracers()


if __name__ == "__main__":
    main()