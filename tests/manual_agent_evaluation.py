from dotenv import load_dotenv

load_dotenv(
    override=True,
)

from langchain_core.tracers.langchain import (
    wait_for_all_tracers,
)

from app.ai.agent.agent import (
    build_agent,
)
from app.ai.agent.model import (
    build_agent_model,
)
from app.core.config import get_settings
from app.evaluation.agent import (
    calculate_agent_evaluation_summary,
    load_agent_golden_cases,
    run_agent_evaluation_case,
    score_agent_evaluation_result,
)


EVALUATION_CASE_IDS = {
    "order-001",
    "order-002",
    "order-003",
    "safety-001",
}


def main() -> None:
    settings = get_settings()

    model = build_agent_model(
        settings,
    )

    agent = build_agent(
        model=model,
    )

    cases = [
        case
        for case
        in load_agent_golden_cases()
        if case.id in EVALUATION_CASE_IDS
    ]

    results = []

    try:
        for case in cases:
            print(
                f"\n===== {case.id} ====="
            )

            result = (
                run_agent_evaluation_case(
                    agent=agent,
                    case=case,
                )
            )

            score = (
                score_agent_evaluation_result(
                    result
                )
            )

            results.append(result)

            print(
                "TOOLS =",
                result.actual_tools,
            )
            print(
                "ANSWER =",
                result.final_answer,
            )
            print(
                "PASSED =",
                score.passed,
            )

        summary = (
            calculate_agent_evaluation_summary(
                results
            )
        )

        print(
            "\n===== AGENT EVALUATION ====="
        )
        print(
            "total_cases =",
            summary.total_cases,
        )
        print(
            "tool_selection_accuracy =",
            summary.tool_selection_accuracy,
        )
        print(
            "answer_constraint_score =",
            summary.answer_constraint_score,
        )
        print(
            "safety_score =",
            summary.safety_score,
        )
        print(
            "overall_pass_rate =",
            summary.overall_pass_rate,
        )

    finally:
        wait_for_all_tracers()


if __name__ == "__main__":
    main()