from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class FusedCandidate:
    chunk_id: UUID
    score: float


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[UUID]],
    *,
    k: int = 60,
) -> list[FusedCandidate]:
    """Fuse ranked chunk lists using Reciprocal Rank Fusion."""

    if k < 0:
        raise ValueError("RRF k must be non-negative")

    scores: dict[UUID, float] = {}

    for ranking in rankings:
        for rank, chunk_id in enumerate(
            ranking,
            start=1,
        ):
            scores[chunk_id] = (
                scores.get(chunk_id, 0.0)
                + 1.0 / (k + rank)
            )

    return [
        FusedCandidate(
            chunk_id=chunk_id,
            score=score,
        )
        for chunk_id, score in sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]