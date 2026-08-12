from dataclasses import dataclass
from typing import Protocol
import hashlib

class Tokenizer(Protocol):
    def encode(self, text: str) -> list[int]:
        ...

    def decode(self, token_ids: list[int]) -> str:
        ...


@dataclass(frozen=True)
class ChunkData:
    ordinal: int
    token_start: int
    token_end: int
    token_count: int
    content: str


def token_chunks(
    text: str,
    tokenizer: Tokenizer,
    max_tokens: int = 420,
    overlap: int = 60,
) -> list[ChunkData]:
    if overlap >= max_tokens:
        raise ValueError("overlap must be smaller than max_tokens")

    token_ids = tokenizer.encode(text)
    step = max_tokens - overlap

    chunks: list[ChunkData] = []

    for ordinal, start in enumerate(
        range(0, len(token_ids), step)
    ):
        end = min(start + max_tokens, len(token_ids))

        content = tokenizer.decode(
            token_ids[start:end]
        ).strip()

        if content:
            chunks.append(
                ChunkData(
                    ordinal=ordinal,
                    token_start=start,
                    token_end=end,
                    token_count=end - start,
                    content=content,
                )
            )

        if end == len(token_ids):
            break

    return chunks


def build_chunk_version(
    content: str,
) -> str:
    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()[:12]