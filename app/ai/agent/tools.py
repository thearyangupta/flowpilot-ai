from langchain.tools import tool

from app.ai.tool_models import LookupOrderArgs
from app.ai.tools.order_tools import (
    lookup_order,
)


@tool(
    "lookup_order",
    args_schema=LookupOrderArgs,
)
def lookup_order_tool(
    order_id: str,
) -> dict:
    """Look up the current status of an order.

    Use this when the user asks about an order
    and provides an order ID in ORD-###### format.
    """

    return lookup_order(
        order_id=order_id,
    )


FLOWPILOT_AGENT_TOOLS = [
    lookup_order_tool,
]