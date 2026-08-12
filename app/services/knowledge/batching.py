from collections.abc import Iterator, Sequence
from typing import TypeVar


T = TypeVar("T")


def batched(
    items: Sequence[T],
    *,
    size: int,
) -> Iterator[Sequence[T]]:
    """Yield items in consecutive batches of at most size elements."""

    if size <= 0:
        raise ValueError("batch size must be greater than zero")

    for start in range(0, len(items), size):
        yield items[start : start + size]