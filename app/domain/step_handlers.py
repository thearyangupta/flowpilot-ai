from typing import Any


def set_value_handler(
    data: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    result = data.copy()

    key = config["key"]
    value = config["value"]

    result[key] = value

    return result


def uppercase_handler(
    data: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    result = data.copy()

    key = config["key"]

    if key not in result:
        raise ValueError(
            f"Cannot uppercase missing key: '{key}'"
        )

    value = result[key]

    if not isinstance(value, str):
        raise ValueError(
            f"Value for key '{key}' must be a string"
        )

    result[key] = value.upper()

    return result


def require_key_handler(
    data: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    key = config["key"]

    if key not in data:
        raise ValueError(
            f"Required key is missing: '{key}'"
        )

    return data.copy()