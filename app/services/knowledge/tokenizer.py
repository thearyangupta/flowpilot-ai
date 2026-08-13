from __future__ import annotations


class WhitespaceTokenizer:
    """Minimal reversible tokenizer for knowledge ingestion."""

    def __init__(self) -> None:
        self._tokens: list[str] = []

    def encode(self, text: str) -> list[int]:
        self._tokens = text.split()

        return list(range(len(self._tokens)))

    def decode(self, token_ids: list[int]) -> str:
        return " ".join(
            self._tokens[token_id]
            for token_id in token_ids
        )