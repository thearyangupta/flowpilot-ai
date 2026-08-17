from app.evaluation.agent import (
    AgentEvaluationResult,
    AgentGoldenCase,
    calculate_agent_evaluation_summary,
    score_agent_evaluation_result,
)


def make_case(
    *,
    case_id: str,
    category: str = "mcp_tool",
    expected_tools: tuple[str, ...] = (
        "lookup_order",
    ),
    required: tuple[str, ...] = (
        "shipped",
    ),
    forbidden: tuple[str, ...] = (
        "delivered",
    ),
) -> AgentGoldenCase:
    return AgentGoldenCase(
        id=case_id,
        category=category,
        input="Check the order.",
        expected_tools=expected_tools,
        expected_answer_contains=required,
        forbidden_answer_contains=forbidden,
    )


def test_agent_result_scores_full_pass() -> None:
    result = AgentEvaluationResult(
        case=make_case(
            case_id="pass-001",
        ),
        actual_tools=(
            "lookup_order",
        ),
        final_answer=(
            "Order ORD-123456 "
            "is shipped."
        ),
    )

    score = (
        score_agent_evaluation_result(
            result
        )
    )

    assert score.tool_selection_ok
    assert score.required_content_ok
    assert score.forbidden_content_ok
    assert score.passed


def test_agent_result_fails_wrong_tool() -> None:
    result = AgentEvaluationResult(
        case=make_case(
            case_id="wrong-tool",
        ),
        actual_tools=(),
        final_answer=(
            "Order ORD-123456 "
            "is shipped."
        ),
    )

    score = (
        score_agent_evaluation_result(
            result
        )
    )

    assert not score.tool_selection_ok
    assert not score.passed


def test_agent_result_fails_forbidden_content() -> None:
    result = AgentEvaluationResult(
        case=make_case(
            case_id="unsafe-001",
            category="safety",
        ),
        actual_tools=(
            "lookup_order",
        ),
        final_answer=(
            "Order ORD-123456 "
            "was delivered."
        ),
    )

    score = (
        score_agent_evaluation_result(
            result
        )
    )

    assert not (
        score.forbidden_content_ok
    )
    assert not score.passed


def test_agent_evaluation_summary() -> None:
    results = [
        AgentEvaluationResult(
            case=make_case(
                case_id="case-1",
            ),
            actual_tools=(
                "lookup_order",
            ),
            final_answer=(
                "The order is shipped."
            ),
        ),
        AgentEvaluationResult(
            case=make_case(
                case_id="case-2",
                category="safety",
            ),
            actual_tools=(),
            final_answer=(
                "The order was delivered."
            ),
        ),
    ]

    summary = (
        calculate_agent_evaluation_summary(
            results
        )
    )

    assert summary.total_cases == 2
    assert (
        summary.tool_selection_accuracy
        == 0.5
    )
    assert (
        summary.answer_constraint_score
        == 0.5
    )
    assert summary.safety_score == 0.0
    assert summary.overall_pass_rate == 0.5