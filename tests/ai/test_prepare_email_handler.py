import pytest

from app.domain.step_handlers import (
    prepare_email_handler,
)


def test_prepare_email_uses_body_when_present():
    result = prepare_email_handler(
        {
            "sender": "customer@example.com",
            "subject": "Refund help",
            "body_text": (
                "I purchased the service "
                "and need a refund."
            ),
            "provider_message_id": "msg-1",
        },
        {},
    )

    assert result["email_text"] == (
        "I purchased the service "
        "and need a refund."
    )


def test_prepare_email_uses_subject_when_body_empty():
    result = prepare_email_handler(
        {
            "sender": "customer@example.com",
            "subject": (
                "Can you help me with my refund?"
            ),
            "body_text": "",
            "provider_message_id": "msg-2",
        },
        {},
    )

    assert result["email_text"] == (
        "Can you help me with my refund?"
    )


def test_prepare_email_rejects_empty_email():
    with pytest.raises(
        ValueError,
        match="Email subject or body_text is required",
    ):
        prepare_email_handler(
            {
                "sender": "customer@example.com",
                "subject": "",
                "body_text": "",
                "provider_message_id": "msg-3",
            },
            {},
        )