from app.evaluation.agent import (
    KNOWN_AGENT_CATEGORIES,
    KNOWN_AGENT_TOOLS,
    load_agent_golden_cases,
)


def test_agent_golden_dataset_is_valid() -> None:
    cases = load_agent_golden_cases()

    assert len(cases) >= 10

    ids = [
        case.id
        for case in cases
    ]

    assert len(ids) == len(set(ids))

    for case in cases:
        assert case.id.strip()
        assert case.input.strip()

        assert (
            case.category
            in KNOWN_AGENT_CATEGORIES
        )

        assert set(
            case.expected_tools
        ).issubset(
            KNOWN_AGENT_TOOLS
        )


def test_agent_golden_dataset_covers_paths() -> None:
    cases = load_agent_golden_cases()

    categories = {
        case.category
        for case in cases
    }

    assert (
        KNOWN_AGENT_CATEGORIES
        <= categories
    )

    covered_tools = {
        tool_name
        for case in cases
        for tool_name in case.expected_tools
    }

    assert (
        covered_tools
        == KNOWN_AGENT_TOOLS
    )


def test_agent_golden_dataset_has_safety_case() -> None:
    cases = load_agent_golden_cases()

    safety_cases = [
        case
        for case in cases
        if case.category == "safety"
    ]

    assert safety_cases

    assert any(
        case.forbidden_answer_contains
        for case in safety_cases
    )