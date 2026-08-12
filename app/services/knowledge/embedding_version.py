from hashlib import sha256

from app.models.knowledge_chunk import KnowledgeChunk
from app.services.knowledge.embedding_provider import Embedder


def embedding_key(
    chunk: KnowledgeChunk,
    embedder: Embedder,
) -> str:
    """Return the identity of the embedding required for this chunk."""

    raw = f"{embedder.model_name}:{chunk.chunk_version}"

    return sha256(
        raw.encode("utf-8")
    ).hexdigest()