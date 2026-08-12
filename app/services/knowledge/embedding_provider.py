from typing import Protocol


class Embedder(Protocol):
    """Boundary for providers that convert text into embedding vectors."""

    model_name: str
    dimensions: int

    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Return one embedding vector for each supplied text."""
        ...