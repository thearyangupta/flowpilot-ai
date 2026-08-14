from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.services.knowledge.embedding_provider import Embedder
from app.services.knowledge.embedding_validation import (
    validate_embeddings,
)
from app.services.knowledge.rrf import (
    reciprocal_rank_fusion,
)


@dataclass(frozen=True)
class SemanticCandidate:
    chunk_id: UUID
    distance: float

@dataclass(frozen=True)
class KeywordCandidate:
    chunk_id: UUID
    rank: float

@dataclass(frozen=True)
class RetrievalHit:
    chunk: KnowledgeChunk
    fused_score: float


def semantic_candidates(
    *,
    db: Session,
    user_id: UUID,
    query_vector: list[float],
    limit: int = 20,
) -> list[SemanticCandidate]:
    distance = KnowledgeChunk.embedding.cosine_distance(
        query_vector
    )

    statement = (
        select(
            KnowledgeChunk.id,
            distance.label("distance"),
        )
        .where(
            KnowledgeChunk.user_id == user_id,
            KnowledgeChunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(limit)
    )

    rows = db.execute(statement).all()

    return [
        SemanticCandidate(
            chunk_id=row.id,
            distance=float(row.distance),
        )
        for row in rows
    ]


def keyword_candidates(
    *,
    db: Session,
    user_id: UUID,
    query: str,
    limit: int = 20,
) -> list[KeywordCandidate]:
    ts_query = func.websearch_to_tsquery(
        "english",
        query,
    )

    search_vector = func.to_tsvector(
        "english",
        KnowledgeChunk.search_vector,
    )

    rank = func.ts_rank_cd(
        KnowledgeChunk.search_vector,
        ts_query,
    )

    statement = (
        select(
            KnowledgeChunk.id,
            rank.label("rank"),
        )
        .where(
            KnowledgeChunk.user_id == user_id,
            search_vector.op("@@")(
                ts_query
            ),
        )
        .order_by(rank.desc())
        .limit(limit)
    )

    rows = db.execute(statement).all()

    return [
        KeywordCandidate(
            chunk_id=row.id,
            rank=float(row.rank),
        )
        for row in rows
    ]

def hybrid_search(
    *,
    db: Session,
    user_id: UUID,
    query: str,
    embedder: Embedder,
    limit: int = 6,
    candidate_limit: int = 20,
) -> list[RetrievalHit]:
    query_vectors = embedder.embed(
        [query]
    )

    validate_embeddings(
        texts=[query],
        vectors=query_vectors,
        dimensions=embedder.dimensions,
    )

    query_vector = query_vectors[0]

    semantic = semantic_candidates(
        db=db,
        user_id=user_id,
        query_vector=query_vector,
        limit=candidate_limit,
    )

    keyword = keyword_candidates(
        db=db,
        user_id=user_id,
        query=query,
        limit=candidate_limit,
    )

    fused = reciprocal_rank_fusion(
        [
            [
                candidate.chunk_id
                for candidate in semantic
            ],
            [
                candidate.chunk_id
                for candidate in keyword
            ],
        ]
    )[:limit]

    if not fused:
        return []

    fused_ids = [
        candidate.chunk_id
        for candidate in fused
    ]

    chunks = list(
        db.scalars(
            select(KnowledgeChunk)
            .where(
                KnowledgeChunk.user_id == user_id,
                KnowledgeChunk.id.in_(fused_ids),
            )
        )
    )

    chunks_by_id = {
        chunk.id: chunk
        for chunk in chunks
    }

    return [
        RetrievalHit(
            chunk=chunks_by_id[candidate.chunk_id],
            fused_score=candidate.score,
        )
        for candidate in fused
        if candidate.chunk_id in chunks_by_id
    ]