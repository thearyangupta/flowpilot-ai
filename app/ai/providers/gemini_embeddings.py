from google import genai
from google.genai import types

from app.ai.providers.gemini_client import build_gemini_client
from app.core.config import Settings
from app.services.knowledge.embedding_errors import (
    PermanentEmbeddingError,
    RetryableEmbeddingError,
)


class GeminiEmbedder:
    model_name = "gemini-embedding-001"
    dimensions = 1536

    def __init__(self, settings: Settings) -> None:
        self._client = build_gemini_client(
            settings
        )

    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        try:
            response = self._client.models.embed_content(
                model=self.model_name,
                contents=texts,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimensions,
                ),
            )

        except Exception as exc:
            raise RetryableEmbeddingError(
                "Gemini embedding request failed."
            ) from exc

        if response.embeddings is None:
            raise PermanentEmbeddingError(
                "Gemini returned no embeddings."
            )

        vectors: list[list[float]] = []

        for embedding in response.embeddings:
            if embedding.values is None:
                raise PermanentEmbeddingError(
                    "Gemini returned an embedding without values."
                )

            vectors.append(
                [float(value) for value in embedding.values]
            )

        return vectors