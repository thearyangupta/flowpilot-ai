class FakeTokenizer:
    def encode(self, text: str) -> list[int]:
        return list(range(len(text.split())))

    def decode(self, token_ids: list[int]) -> str:
        return " ".join(f"token{i}" for i in token_ids)


def test_token_chunks_respect_max_tokens():
    from app.services.knowledge.chunking_service import token_chunks

    tokenizer = FakeTokenizer()

    text = " ".join(f"word{i}" for i in range(1000))

    chunks = token_chunks(
        text=text,
        tokenizer=tokenizer,
        max_tokens=100,
        overlap=20,
    )

    assert chunks
    assert all(chunk.token_count <= 100 for chunk in chunks)


def test_token_chunks_have_expected_overlap():
    from app.services.knowledge.chunking_service import token_chunks

    tokenizer = FakeTokenizer()

    text = " ".join(f"word{i}" for i in range(300))

    chunks = token_chunks(
        text=text,
        tokenizer=tokenizer,
        max_tokens=100,
        overlap=20,
    )

    assert len(chunks) == 4

    assert chunks[0].token_start == 0
    assert chunks[0].token_end == 100

    assert chunks[1].token_start == 80
    assert chunks[1].token_end == 180

    assert chunks[2].token_start == 160
    assert chunks[2].token_end == 260

    assert chunks[3].token_start == 240
    assert chunks[3].token_end == 300


def test_token_chunks_have_stable_ordinals_and_offsets():
    from app.services.knowledge.chunking_service import token_chunks

    tokenizer = FakeTokenizer()

    text = " ".join(f"word{i}" for i in range(250))

    chunks = token_chunks(
        text=text,
        tokenizer=tokenizer,
        max_tokens=100,
        overlap=20,
    )

    assert [chunk.ordinal for chunk in chunks] == [0, 1, 2]

    assert [
        (chunk.token_start, chunk.token_end)
        for chunk in chunks
    ] == [
        (0, 100),
        (80, 180),
        (160, 250),
]

    assert all(
        chunk.token_count == chunk.token_end - chunk.token_start
        for chunk in chunks
)




def test_build_chunk_version_is_deterministic():
    from app.services.knowledge.chunking_service import build_chunk_version

    first = build_chunk_version(
        embedding_model="model-a",
        content="hello world",
    )

    second = build_chunk_version(
        embedding_model="model-a",
        content="hello world",
    )

    assert first == second
    assert len(first) == 12


def test_build_chunk_version_changes_when_model_or_content_changes():
    from app.services.knowledge.chunking_service import build_chunk_version

    base = build_chunk_version("model-a", "hello world")

    different_model = build_chunk_version(
        "model-b",
        "hello world",
    )

    different_content = build_chunk_version(
        "model-a",
        "different content",
    )

    assert base != different_model
    assert base != different_content