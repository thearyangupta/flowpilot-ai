from app.ai.tool_dispatcher import ALLOWED_TOOLS
from app.ai.tool_models import LookupOrderArgs


def execute_requested_tool(call) -> dict:
    tool = ALLOWED_TOOLS.get(call.name)

    if tool is None:
        raise ValueError(f"Tool '{call.name}' is not allowed.")

    args = LookupOrderArgs.model_validate(call.args)

    return tool(**args.model_dump())