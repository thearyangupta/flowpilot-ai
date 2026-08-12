from types import SimpleNamespace

from app.services.knowledge.embedding_version import embedding_key


def test_embedding_key_is_deterministic():
    chunk = SimpleNamespace(
        chunk_version="abc123",
    )

    embedder = SimpleNamespace(
        model_name="model-a",
    )

    first = embedding_key(chunk, embedder)
    second = embedding_key(chunk, embedder)

    assert first == second


def test_embedding_key_changes_when_model_changes():
    chunk = SimpleNamespace(
        chunk_version="abc123",
    )

    embedder_a = SimpleNamespace(
        model_name="model-a",
    )

    embedder_b = SimpleNamespace(
        model_name="model-b",
    )

    assert embedding_key(
        chunk,
        embedder_a,
    ) != embedding_key(
        chunk,
        embedder_b,
    )


def test_embedding_key_changes_when_input_version_changes():
    embedder = SimpleNamespace(
        model_name="model-a",
    )

    chunk_a = SimpleNamespace(
        chunk_version="abc123",
    )

    chunk_b = SimpleNamespace(
        chunk_version="def456",
    )

    assert embedding_key(
        chunk_a,
        embedder,
    ) != embedding_key(
        chunk_b,
        embedder,
    )