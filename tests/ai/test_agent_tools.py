from app.ai.agent.tools import (
    lookup_order_tool,
)


def test_lookup_order_tool_returns_status() -> None:
    result = lookup_order_tool.invoke(
        {
            "order_id": "ORD-123456",
        }
    )

    assert result == {
        "order_id": "ORD-123456",
        "status": "shipped",
    }


def test_lookup_order_tool_returns_not_found() -> None:
    result = lookup_order_tool.invoke(
        {
            "order_id": "ORD-999999",
        }
    )

    assert result == {
        "order_id": "ORD-999999",
        "status": "not_found",
    }