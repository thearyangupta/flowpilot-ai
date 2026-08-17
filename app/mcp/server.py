from mcp.server import MCPServer

from app.ai.tools.order_tools import (
    lookup_order as lookup_order_service,
)


mcp = MCPServer(
    "FlowPilot",
)


@mcp.tool()
def lookup_order(
    order_id: str,
) -> dict[str, str]:
    """Look up the current status of a FlowPilot order.

    The order ID must use the ORD-###### format.
    """

    return lookup_order_service(
        order_id=order_id,
    )


if __name__ == "__main__":
    mcp.run()