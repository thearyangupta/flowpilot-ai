from collections.abc import Sequence

from app.services.knowledge.embedding_errors import (
    PermanentEmbeddingError,
)


class EmbeddingValidationError(PermanentEmbeddingError):
    """Raised when an embedding provider returns an invalid response."""


def validate_embeddings(
    *,
    texts: Sequence[str],
    vectors: Sequence[Sequence[float]],
    dimensions: int,
) -> None:
    """Validate embedding response cardinality and vector dimensions."""

    if len(vectors) != len(texts):
        raise EmbeddingValidationError(
            "embedding count mismatch: "
            f"expected {len(texts)}, got {len(vectors)}"
        )

    for index, vector in enumerate(vectors):
        if len(vector) != dimensions:
            raise EmbeddingValidationError(
                "embedding dimension mismatch: "
                f"vector {index} expected {dimensions}, got {len(vector)}"
            )