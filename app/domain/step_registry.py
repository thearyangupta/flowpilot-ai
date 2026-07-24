from collections.abc import Callable
from typing import Any


StepHandler = Callable[
    [dict[str, Any], dict[str, Any]],
    dict[str, Any],
]


_STEP_REGISTRY: dict[str, StepHandler] = {}


def register_step(
    step_type: str,
    handler: StepHandler,
) -> None:
    normalized_step_type = step_type.strip()

    if not normalized_step_type:
        raise ValueError("Step type cannot be empty")

    if normalized_step_type in _STEP_REGISTRY:
        raise ValueError(
            f"Step type '{normalized_step_type}' "
            "is already registered"
        )

    _STEP_REGISTRY[normalized_step_type] = handler


def get_step_handler(step_type: str) -> StepHandler:
    handler = _STEP_REGISTRY.get(step_type)

    if handler is None:
        raise ValueError(
            f"Unsupported step type: '{step_type}'"
        )

    return handler


def is_step_registered(step_type: str) -> bool:
    return step_type in _STEP_REGISTRY


def get_registered_step_types() -> frozenset[str]:
    return frozenset(_STEP_REGISTRY)


from app.domain.step_handlers import (
    require_key_handler,
    set_value_handler,
    uppercase_handler,
)


register_step("set_value", set_value_handler)
register_step("uppercase", uppercase_handler)
register_step("require_key", require_key_handler)