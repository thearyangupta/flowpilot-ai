from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from app.domain.step_handlers import (
    require_key_handler,
    set_value_handler,
    uppercase_handler,
)

if TYPE_CHECKING:
    from app.ai.decision_service import DecisionService


StepHandler = Callable[
    [dict[str, Any], dict[str, Any]],
    dict[str, Any],
]


_STEP_REGISTRY: dict[str, StepHandler] = {}
_RUNTIME_STEP_TYPES = frozenset(
    {
        "classify_email",
    }
)

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


def get_step_handler(
    step_type: str,
    registry: dict[str, StepHandler] | None = None,
) -> StepHandler:
    active_registry = (
        registry
        if registry is not None
        else _STEP_REGISTRY
    )

    handler = active_registry.get(step_type)

    if handler is None:
        raise ValueError(
            f"Unsupported step type: '{step_type}'"
        )

    return handler


def is_step_registered(step_type: str) -> bool:
    return (
        step_type in _STEP_REGISTRY
        or step_type in _RUNTIME_STEP_TYPES
    )


def get_registered_step_types() -> frozenset[str]:
    return frozenset(_STEP_REGISTRY) | _RUNTIME_STEP_TYPES


def build_step_registry(
    decision_service: "DecisionService",
) -> dict[str, StepHandler]:
    registry = _STEP_REGISTRY.copy()

    def classify_email_handler(
        data: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        input_key = config.get(
            "input_key",
            "email_text",
        )

        output_key = config.get(
            "output_key",
            "decision",
        )

        if input_key not in data:
            raise ValueError(
                f"Email input key is missing: '{input_key}'"
            )

        email_text = data[input_key]

        if not isinstance(email_text, str):
            raise ValueError(
                f"Value for key '{input_key}' must be a string"
            )

        decision = decision_service.classify(
            email_text
        )

        result = data.copy()

        result[output_key] = decision.model_dump(
            mode="json"
        )

        return result

    registry["classify_email"] = (
        classify_email_handler
    )

    return registry


register_step("set_value", set_value_handler)
register_step("uppercase", uppercase_handler)
register_step("require_key", require_key_handler)