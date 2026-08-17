from app.ai.agent.mcp_tools import (
    lookup_order_mcp_tool,
)


def test_langchain_tool_calls_mcp_server() -> None:
    result = lookup_order_mcp_tool.invoke(
        {
            "order_id": "ORD-123456",
        }
    )

    assert result == {
        "order_id": "ORD-123456",
        "status": "shipped",
    }


def test_langchain_tool_gets_mcp_not_found() -> None:
    result = lookup_order_mcp_tool.invoke(
        {
            "order_id": "ORD-999999",
        }
    )

    assert result == {
        "order_id": "ORD-999999",
        "status": "not_found",
    }