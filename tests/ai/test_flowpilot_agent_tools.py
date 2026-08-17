from types import SimpleNamespace
from uuid import uuid4

from app.ai.agent.flowpilot_tools import (
    build_flowpilot_tools,
)


def test_list_projects_is_bound_to_user(
    monkeypatch,
) -> None:
    expected_user_id = uuid4()

    project = SimpleNamespace(
        id=uuid4(),
        name="Recruiter Demo",
    )

    calls = []

    def fake_get_all(
        db,
        user_id,
    ):
        calls.append(
            {
                "db": db,
                "user_id": user_id,
            }
        )

        return [project]

    monkeypatch.setattr(
        "app.ai.agent.flowpilot_tools."
        "project_service.get_all",
        fake_get_all,
    )

    fake_db = object()
    fake_settings = object()

    tools = build_flowpilot_tools(
        db=fake_db,
        user_id=expected_user_id,
        settings=fake_settings,
    )

    list_projects = next(
        tool
        for tool in tools
        if tool.name == "list_projects"
    )

    result = list_projects.invoke({})

    assert calls == [
        {
            "db": fake_db,
            "user_id": expected_user_id,
        }
    ]

    assert result == [
        {
            "id": str(project.id),
            "name": "Recruiter Demo",
        }
    ]


def test_search_knowledge_is_bound_to_user(
    monkeypatch,
) -> None:
    expected_user_id = uuid4()

    chunk = SimpleNamespace(
        id=uuid4(),
        content="Refunds take five business days.",
    )

    hit = SimpleNamespace(
        chunk=chunk,
        fused_score=0.91,
    )

    captured = {}

    class FakeEmbedder:
        dimensions = 1536

    monkeypatch.setattr(
        "app.ai.agent.flowpilot_tools."
        "GeminiEmbedder",
        lambda settings: FakeEmbedder(),
    )

    def fake_hybrid_search(**kwargs):
        captured.update(kwargs)
        return [hit]

    monkeypatch.setattr(
        "app.ai.agent.flowpilot_tools."
        "hybrid_search",
        fake_hybrid_search,
    )

    fake_db = object()
    fake_settings = object()

    tools = build_flowpilot_tools(
        db=fake_db,
        user_id=expected_user_id,
        settings=fake_settings,
    )

    search_knowledge = next(
        tool
        for tool in tools
        if tool.name == "search_knowledge"
    )

    result = search_knowledge.invoke(
        {
            "query": "refund policy",
        }
    )

    assert captured["db"] is fake_db
    assert (
        captured["user_id"]
        == expected_user_id
    )
    assert (
        captured["query"]
        == "refund policy"
    )

    assert result == [
        {
            "chunk_id": str(chunk.id),
            "content":
                "Refunds take five business days.",
            "score": 0.91,
        }
    ]