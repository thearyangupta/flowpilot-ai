import pytest

from mcp import Client

from app.mcp.server import mcp


@pytest.mark.anyio
async def test_mcp_server_lists_lookup_order_tool() -> None:
    async with Client(
        mcp,
        raise_exceptions=True,
    ) as client:
        result = await client.list_tools()

    tool_names = [
        tool.name
        for tool in result.tools
    ]

    assert "lookup_order" in tool_names


@pytest.mark.anyio
async def test_mcp_client_calls_lookup_order() -> None:
    async with Client(
        mcp,
        raise_exceptions=True,
    ) as client:
        result = await client.call_tool(
            "lookup_order",
            {
                "order_id": "ORD-123456",
            },
        )

    assert result.is_error is False

    assert result.structured_content == {
        "order_id": "ORD-123456",
        "status": "shipped",
    }


@pytest.mark.anyio
async def test_mcp_client_gets_not_found_order() -> None:
    async with Client(
        mcp,
        raise_exceptions=True,
    ) as client:
        result = await client.call_tool(
            "lookup_order",
            {
                "order_id": "ORD-999999",
            },
        )

    assert result.is_error is False

    assert result.structured_content == {
        "order_id": "ORD-999999",
        "status": "not_found",
    }