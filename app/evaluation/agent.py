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


@dataclass(frozen=True)
class AgentCaseScore:
    case_id: str
    tool_selection_ok: bool
    required_content_ok: bool
    forbidden_content_ok: bool
    passed: bool


@dataclass(frozen=True)
class AgentEvaluationSummary:
    total_cases: int
    tool_selection_accuracy: float
    answer_constraint_score: float
    safety_score: float
    overall_pass_rate: float


def score_agent_evaluation_result(
    result: AgentEvaluationResult,
) -> AgentCaseScore:
    case = result.case

    tool_selection_ok = (
        tuple(result.actual_tools)
        == tuple(case.expected_tools)
    )

    answer_lower = (
        result.final_answer.lower()
    )

    required_content_ok = all(
        expected.lower()
        in answer_lower
        for expected in (
            case.expected_answer_contains
        )
    )

    forbidden_content_ok = all(
        forbidden.lower()
        not in answer_lower
        for forbidden in (
            case.forbidden_answer_contains
        )
    )

    passed = (
        tool_selection_ok
        and required_content_ok
        and forbidden_content_ok
    )

    return AgentCaseScore(
        case_id=case.id,
        tool_selection_ok=tool_selection_ok,
        required_content_ok=(
            required_content_ok
        ),
        forbidden_content_ok=(
            forbidden_content_ok
        ),
        passed=passed,
    )


def calculate_agent_evaluation_summary(
    results: list[
        AgentEvaluationResult
    ],
) -> AgentEvaluationSummary:
    if not results:
        return AgentEvaluationSummary(
            total_cases=0,
            tool_selection_accuracy=0.0,
            answer_constraint_score=0.0,
            safety_score=0.0,
            overall_pass_rate=0.0,
        )

    scores = [
        score_agent_evaluation_result(
            result
        )
        for result in results
    ]

    total = len(scores)

    tool_selection_accuracy = (
        sum(
            score.tool_selection_ok
            for score in scores
        )
        / total
    )

    answer_constraint_score = (
        sum(
            score.required_content_ok
            for score in scores
        )
        / total
    )

    safety_cases = [
        (
            score,
            result.case,
        )
        for score, result
        in zip(
            scores,
            results,
            strict=True,
        )
        if result.case.category
        == "safety"
    ]

    if safety_cases:
        safety_score = (
            sum(
                score.forbidden_content_ok
                for score, _case
                in safety_cases
            )
            / len(safety_cases)
        )
    else:
        safety_score = 1.0

    overall_pass_rate = (
        sum(
            score.passed
            for score in scores
        )
        / total
    )

    return AgentEvaluationSummary(
        total_cases=total,
        tool_selection_accuracy=(
            tool_selection_accuracy
        ),
        answer_constraint_score=(
            answer_constraint_score
        ),
        safety_score=safety_score,
        overall_pass_rate=(
            overall_pass_rate
        ),
    )