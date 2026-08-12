from dataclasses import dataclass
from uuid import UUID
from collections.abc import Sequence
from typing import Protocol
from math import ceil


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    expected_document_ids: frozenset[UUID]
    answerable: bool


class RetrievalHitLike(Protocol):
    document_id: UUID


@dataclass(frozen=True)
class RetrievalEvaluationConfig:
    evaluation_version: str
    embedding_model: str
    embedding_dimensions: int
    top_k: int
    candidate_limit: int
    rrf_k: int


@dataclass(frozen=True)
class RetrievalEvaluationReport:
    config: RetrievalEvaluationConfig
    mean_recall_at_k: float
    citation_validity_rate: float
    unsupported_refusal_rate: float
    retrieval_p50_ms: float
    retrieval_p95_ms: float


@dataclass(frozen=True)
class RetrievalCaseResult:
    case: RetrievalCase
    retrieved_document_ids: tuple[UUID, ...]
    citation_ids: tuple[str, ...]
    allowed_source_ids: frozenset[str]
    needs_knowledge: bool
    retrieval_latency_ms: float

@dataclass(frozen=True)
class _EvaluationDocumentHit:
    document_id: UUID


def recall_at_k(
    expected_document_ids: frozenset[UUID],
    hits: Sequence[RetrievalHitLike],
    *,
    k: int,
) -> float:
    """Return document-level Recall@k for a retrieval result."""

    if k <= 0:
        raise ValueError("k must be greater than zero")

    if not expected_document_ids:
        return 1.0

    returned_document_ids = {
        hit.document_id
        for hit in hits[:k]
    }

    matched = (
        expected_document_ids
        & returned_document_ids
    )

    return (
        len(matched)
        / len(expected_document_ids)
    )


def citations_are_valid(
    *,
    citation_ids: list[str],
    allowed_source_ids: set[str] | frozenset[str],
) -> bool:
    """Return whether citations are non-empty and belong to the allow-list."""

    if not citation_ids:
        return False

    return all(
        citation_id in allowed_source_ids
        for citation_id in citation_ids
    )


def citation_validity_rate(
    results: list[bool],
) -> float:
    """Return the fraction of evaluated outputs with valid citations."""

    if not results:
        return 0.0

    return (
        sum(results)
        / len(results)
    )


def unsupported_refusal_rate(
    results: list[bool],
) -> float:
    """Return the fraction of unanswerable cases correctly refused."""

    if not results:
        return 1.0

    return (
        sum(results)
        / len(results)
    )


def percentile(
    values: list[float],
    percentile_value: float,
) -> float:
    if not values:
        return 0.0

    if not 0.0 <= percentile_value <= 1.0:
        raise ValueError(
            "percentile must be between 0.0 and 1.0"
        )

    ordered = sorted(values)

    index = max(
        0,
        ceil(percentile_value * len(ordered)) - 1,
    )

    return ordered[index]


def latency_percentiles(
    latencies_ms: list[float],
) -> tuple[float, float]:
    return (
        percentile(latencies_ms, 0.50),
        percentile(latencies_ms, 0.95),
    )


def build_evaluation_report(
    *,
    config: RetrievalEvaluationConfig,
    results: list[RetrievalCaseResult],
) -> RetrievalEvaluationReport:
    recall_scores: list[float] = []
    citation_results: list[bool] = []
    refusal_results: list[bool] = []
    latencies: list[float] = []

    for result in results:
        retrieval_hits = [
            _EvaluationDocumentHit(
                document_id=document_id,
            )
            for document_id in result.retrieved_document_ids
        ]

        if result.case.answerable:
            recall_scores.append(
                recall_at_k(
                    result.case.expected_document_ids,
                    retrieval_hits,
                    k=config.top_k,
                )
            )

            citation_results.append(
                citations_are_valid(
                    citation_ids=list(
                        result.citation_ids
                    ),
                    allowed_source_ids=(
                        result.allowed_source_ids
                    ),
                )
            )

        else:
            refusal_results.append(
                result.needs_knowledge
            )

        latencies.append(
            result.retrieval_latency_ms
        )

    mean_recall = (
        sum(recall_scores) / len(recall_scores)
        if recall_scores
        else 0.0
    )

    p50, p95 = latency_percentiles(
        latencies
    )

    return RetrievalEvaluationReport(
        config=config,
        mean_recall_at_k=mean_recall,
        citation_validity_rate=(
            citation_validity_rate(
                citation_results
            )
        ),
        unsupported_refusal_rate=(
            unsupported_refusal_rate(
                refusal_results
            )
        ),
        retrieval_p50_ms=p50,
        retrieval_p95_ms=p95,
    )