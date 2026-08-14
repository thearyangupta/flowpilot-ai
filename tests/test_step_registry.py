import pytest

from app.domain.step_handlers import (
    require_key_handler,
    set_value_handler,
    uppercase_handler,
)
from app.domain.step_registry import (
    get_registered_step_types,
    get_step_handler,
    is_step_registered,
    register_step,
)


def test_builtin_steps_are_registered() -> None:
    registered_steps = get_registered_step_types()

    assert registered_steps == frozenset(
        {
            "set_value",
            "uppercase",
            "require_key",
            "prepare_email",
            "classify_email",
            "create_reply_draft",
        }
    )

def test_registry_returns_correct_handler() -> None:
    handler = get_step_handler("uppercase")

    assert handler is uppercase_handler


def test_registered_step_is_recognized() -> None:
    assert is_step_registered("set_value") is True


def test_unknown_step_is_not_registered() -> None:
    assert is_step_registered("send_email") is False


def test_unsupported_handler_lookup_fails() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported step type",
    ):
        get_step_handler("send_email")


def test_duplicate_registration_fails() -> None:
    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        register_step(
            "uppercase",
            uppercase_handler,
        )


def test_set_value_returns_updated_context() -> None:
    original_context = {
        "name": "Aryan",
    }

    result = set_value_handler(
        original_context,
        {
            "key": "role",
            "value": "developer",
        },
    )

    assert result == {
        "name": "Aryan",
        "role": "developer",
    }


def test_set_value_does_not_mutate_input_context() -> None:
    original_context = {
        "name": "Aryan",
    }

    set_value_handler(
        original_context,
        {
            "key": "role",
            "value": "developer",
        },
    )

    assert original_context == {
        "name": "Aryan",
    }


def test_uppercase_returns_updated_context() -> None:
    result = uppercase_handler(
        {
            "name": "aryan",
        },
        {
            "key": "name",
        },
    )

    assert result == {
        "name": "ARYAN",
    }


def test_uppercase_is_deterministic() -> None:
    context = {
        "name": "aryan",
    }
    config = {
        "key": "name",
    }

    first_result = uppercase_handler(context, config)
    second_result = uppercase_handler(context, config)

    assert first_result == second_result


def test_uppercase_fails_for_missing_key() -> None:
    with pytest.raises(
        ValueError,
        match="Cannot uppercase missing key",
    ):
        uppercase_handler(
            {},
            {
                "key": "name",
            },
        )


def test_uppercase_fails_for_non_string_value() -> None:
    with pytest.raises(
        ValueError,
        match="must be a string",
    ):
        uppercase_handler(
            {
                "age": 22,
            },
            {
                "key": "age",
            },
        )


def test_require_key_returns_context_when_key_exists() -> None:
    original_context = {
        "email": "aryan@example.com",
    }

    result = require_key_handler(
        original_context,
        {
            "key": "email",
        },
    )

    assert result == original_context
    assert result is not original_context


def test_require_key_fails_when_key_is_missing() -> None:
    with pytest.raises(
        ValueError,
        match="Required key is missing",
    ):
        require_key_handler(
            {},
            {
                "key": "email",
            },
        )