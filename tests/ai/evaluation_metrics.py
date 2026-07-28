from dataclasses import dataclass

from app.ai.schemas import EmailDecision, Intent, Urgency


@dataclass(frozen=True) #frozen = True : means the evaluation record cannot accidentally be changed after creation
class EvaluationResult:
    expected_intent: Intent
    expected_urgency: Urgency
    actual_decision: EmailDecision


@dataclass(frozen=True)
class EvaluationSummary:
    total_cases: int
    schema_valid_rate: float
    intent_accuracy: float
    urgency_accuracy: float
    fallback_rate: float


def calculate_evaluation_summary(
    results: list[EvaluationResult],
) -> EvaluationSummary:
    total_cases = len(results)

    if total_cases == 0:
        return EvaluationSummary(
            total_cases=0,
            schema_valid_rate=0.0,
            intent_accuracy=0.0,
            urgency_accuracy=0.0,
            fallback_rate=0.0,
        )

    schema_valid_count = sum(
        isinstance(
            result.actual_decision,
            EmailDecision,
        )
        for result in results
    )

    correct_intent_count = sum(
        result.actual_decision.intent
        == result.expected_intent
        for result in results
    )

    correct_urgency_count = sum(
        result.actual_decision.urgency
        == result.expected_urgency
        for result in results
    )

    fallback_count = sum(
        result.actual_decision.needs_human_review
        for result in results
    )

    return EvaluationSummary(
        total_cases=total_cases,
        schema_valid_rate=(
            schema_valid_count / total_cases
        ),
        intent_accuracy=(
            correct_intent_count / total_cases
        ),
        urgency_accuracy=(
            correct_urgency_count / total_cases
        ),
        fallback_rate=(
            fallback_count / total_cases
        ),
    )