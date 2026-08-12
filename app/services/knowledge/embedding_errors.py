class EmbeddingError(Exception):
    """Base error for knowledge embedding failures."""


class RetryableEmbeddingError(EmbeddingError):
    """Embedding failure that may succeed when retried later."""


class PermanentEmbeddingError(EmbeddingError):
    """Embedding failure that should not be retried automatically."""