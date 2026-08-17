import asyncio

from langchain.tools import tool
from mcp import Client

from app.ai.tool_models import LookupOrderArgs
from app.mcp.server import mcp


async def call_mcp_lookup_order(
    *,
    order_id: str,
) -> dict[str, str]:
    async with Client(
        mcp,
        raise_exceptions=True,
    ) as client:
        result = await client.call_tool(
            "lookup_order",
            {
                "order_id": order_id,
            },
        )

    if result.is_error:
        raise RuntimeError(
            "MCP lookup_order tool failed"
        )

    structured = result.structured_content

    if not isinstance(
        structured,
        dict,
    ):
        raise RuntimeError(
            "MCP lookup_order returned "
            "invalid structured content"
        )

    order_id_value = structured.get(
        "order_id"
    )

    status_value = structured.get(
        "status"
    )

    if (
        not isinstance(
            order_id_value,
            str,
        )
        or not isinstance(
            status_value,
            str,
        )
    ):
        raise RuntimeError(
            "MCP lookup_order returned "
            "invalid order data"
        )

    return {
        "order_id": order_id_value,
        "status": status_value,
    }


@tool(
    "lookup_order",
    args_schema=LookupOrderArgs,
)
def lookup_order_mcp_tool(
    order_id: str,
) -> dict[str, str]:
    """Look up an order through the FlowPilot MCP server.

    Use this when the user asks for the current
    status of an order in ORD-###### format.
    """

    return asyncio.run(
        call_mcp_lookup_order(
            order_id=order_id,
        )
    )


MCP_AGENT_TOOLS = [
    lookup_order_mcp_tool,
]