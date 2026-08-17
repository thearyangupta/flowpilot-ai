import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_core.messages import ToolMessage

KNOWN_AGENT_TOOLS = frozenset(
    {
        "list_projects",
        "search_knowledge",
        "lookup_order",
    }
)

KNOWN_AGENT_CATEGORIES = frozenset(
    {
        "direct",
        "flowpilot_tool",
        "mcp_tool",
        "safety",
    }
)


@dataclass(frozen=True)
class AgentGoldenCase:
    id: str
    category: str
    input: str
    expected_tools: tuple[str, ...]
    expected_answer_contains: tuple[str, ...]
    forbidden_answer_contains: tuple[str, ...]


def default_agent_dataset_path() -> Path:
    return (
        Path(__file__).parent
        / "data"
        / "agent_golden.jsonl"
    )


def load_agent_golden_cases(
    path: Path | None = None,
) -> list[AgentGoldenCase]:
    dataset_path = (
        path
        if path is not None
        else default_agent_dataset_path()
    )

    cases: list[AgentGoldenCase] = []

    for line in dataset_path.read_text(
        encoding="utf-8",
    ).splitlines():
        if not line.strip():
            continue

        payload = json.loads(line)

        case = AgentGoldenCase(
            id=payload["id"],
            category=payload["category"],
            input=payload["input"],
            expected_tools=tuple(
                payload["expected_tools"]
            ),
            expected_answer_contains=tuple(
                payload[
                    "expected_answer_contains"
                ]
            ),
            forbidden_answer_contains=tuple(
                payload[
                    "forbidden_answer_contains"
                ]
            ),
        )

        cases.append(case)

    return cases


@dataclass(frozen=True)
class AgentEvaluationResult:
    case: AgentGoldenCase
    actual_tools: tuple[str, ...]
    final_answer: str


def extract_tool_names(
    result: dict[str, Any],
) -> tuple[str, ...]:
    messages = result["messages"]

    return tuple(
        message.name
        for message in messages
        if isinstance(
            message,
            ToolMessage,
        )
        and message.name
    )


def extract_final_answer(
    result: dict[str, Any],
) -> str:
    messages = result["messages"]

    if not messages:
        return ""

    final_message = messages[-1]

    content = final_message.content

    if isinstance(
        content,
        str,
    ):
        return content

    return str(content)


def run_agent_evaluation_case(
    *,
    agent,
    case: AgentGoldenCase,
) -> AgentEvaluationResult:
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": case.input,
                }
            ]
        }
    )

    return AgentEvaluationResult(
        case=case,
        actual_tools=extract_tool_names(
            result
        ),
        final_answer=extract_final_answer(
            result
        ),
    )