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


def prepare_email_handler(
    data: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    sender = str(
        data.get("sender") or ""
    ).strip()

    subject = str(
        data.get("subject") or ""
    ).strip()

    body_text = str(
        data.get("body_text") or ""
    ).strip()

    provider_message_id = str(
        data.get("provider_message_id") or ""
    ).strip()

    if not sender:
        raise ValueError(
            "Email sender is required"
        )

    if not body_text:
        raise ValueError(
            "Email body_text is required"
        )

    if not provider_message_id:
        raise ValueError(
            "Email provider_message_id is required"
        )

    result = data.copy()

    result["email_text"] = "\n".join(
        part
        for part in (
            subject,
            body_text,
        )
        if part
    )

    result["source_message"] = {
        "sender": sender,
        "subject": subject,
        "body_text": body_text,
        "message_id": provider_message_id,
    }

    return result