from types import SimpleNamespace
from uuid import uuid4

from app.ai.agent.gmail_tools import (
    build_gmail_agent_tools,
)


class FakeExecutable:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class FakeMessages:
    def __init__(self, raw_message):
        self.raw_message = raw_message
        self.list_calls = []
        self.get_calls = []

    def list(self, **kwargs):
        self.list_calls.append(kwargs)

        return FakeExecutable(
            {
                "messages": [
                    {
                        "id": "gmail-message-1",
                    }
                ]
            }
        )

    def get(self, **kwargs):
        self.get_calls.append(kwargs)

        return FakeExecutable(
            self.raw_message
        )


class FakeUsers:
    def __init__(self, messages):
        self._messages = messages

    def messages(self):
        return self._messages


class FakeGmail:
    def __init__(self, messages):
        self._users = FakeUsers(messages)

    def users(self):
        return self._users


def test_search_gmail_messages_reads_connected_user(
    monkeypatch,
) -> None:
    expected_user_id = uuid4()
    fake_db = object()

    raw_message = {
        "id": "gmail-message-1",
        "threadId": "gmail-thread-1",
        "payload": {
            "headers": [
                {
                    "name": "From",
                    "value": "sender@example.com",
                },
                {
                    "name": "Subject",
                    "value":
                        "FlowPilot OAuth Verification Test",
                },
            ],
            "mimeType": "text/plain",
            "body": {
                "data":
                    "SGVsbG8gRnJvbSBHbWFpbA==",
            },
        },
    }

    fake_messages = FakeMessages(
        raw_message
    )
    fake_gmail = FakeGmail(
        fake_messages
    )

    provider_calls = []

    def fake_build_gmail_client(
        db,
        *,
        user_id,
    ):
        provider_calls.append(
            {
                "db": db,
                "user_id": user_id,
            }
        )

        return fake_gmail

    monkeypatch.setattr(
        "app.ai.agent.gmail_tools."
        "build_gmail_client",
        fake_build_gmail_client,
    )

    tools = build_gmail_agent_tools(
        db=fake_db,
        user_id=expected_user_id,
    )

    search_tool = next(
        tool
        for tool in tools
        if tool.name
        == "search_gmail_messages"
    )

    result = search_tool.invoke(
        {
            "query":
                'subject:"FlowPilot OAuth Verification Test"',
        }
    )

    assert provider_calls == [
        {
            "db": fake_db,
            "user_id": expected_user_id,
        }
    ]

    assert fake_messages.list_calls == [
        {
            "userId": "me",
            "q":
                'subject:"FlowPilot OAuth Verification Test"',
            "maxResults": 5,
        }
    ]

    assert fake_messages.get_calls == [
        {
            "userId": "me",
            "id": "gmail-message-1",
            "format": "full",
        }
    ]

    assert result == [
        {
            "message_id":
                "gmail-message-1",
            "thread_id":
                "gmail-thread-1",
            "sender":
                "sender@example.com",
            "subject":
                "FlowPilot OAuth Verification Test",
            "body":
                "Hello From Gmail",
        }
    ]


def test_create_gmail_draft_is_bound_to_user(
    monkeypatch,
) -> None:
    expected_user_id = uuid4()
    fake_db = object()

    captured = {}

    def fake_create_gmail_draft(
        db,
        *,
        user_id,
        message,
    ):
        captured["db"] = db
        captured["user_id"] = user_id
        captured["to"] = message["To"]
        captured["subject"] = message[
            "Subject"
        ]
        captured["body"] = (
            message.get_content().strip()
        )

        return {
            "id": "draft-123",
            "message": {
                "id": "message-456",
            },
        }

    monkeypatch.setattr(
        "app.ai.agent.gmail_tools."
        "create_gmail_draft",
        fake_create_gmail_draft,
    )

    tools = build_gmail_agent_tools(
        db=fake_db,
        user_id=expected_user_id,
    )

    draft_tool = next(
        tool
        for tool in tools
        if tool.name
        == "create_gmail_draft"
    )

    result = draft_tool.invoke(
        {
            "recipient":
                "recipient@example.com",
            "subject":
                "FlowPilot OAuth Verification Reply",
            "body":
                "This draft was created by FlowPilot.",
        }
    )

    assert captured == {
        "db": fake_db,
        "user_id": expected_user_id,
        "to": "recipient@example.com",
        "subject":
            "FlowPilot OAuth Verification Reply",
        "body":
            "This draft was created by FlowPilot.",
    }

    assert result == {
        "draft_id": "draft-123",
        "message_id": "message-456",
        "status": "draft_created",
    }
