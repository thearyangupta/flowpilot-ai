from uuid import UUID

from email.message import EmailMessage

from langchain.tools import tool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.google.gmail_draft_service import (
    create_gmail_draft,
)
from app.services.google.gmail_message_service import (
    normalize_gmail_message,
)
from app.services.google.google_provider_service import (
    build_gmail_client,
)


class SearchGmailArgs(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=500,
        description=(
            "A Gmail search query, such as "
            'subject:"FlowPilot OAuth Verification Test"'
        ),
    )


class CreateGmailDraftArgs(BaseModel):
    recipient: str = Field(
        min_length=3,
        max_length=320,
    )
    subject: str = Field(
        min_length=1,
        max_length=500,
    )
    body: str = Field(
        min_length=1,
        max_length=10000,
    )


def build_gmail_agent_tools(
    *,
    db: Session,
    user_id: UUID,
):
    @tool(
        "search_gmail_messages",
        args_schema=SearchGmailArgs,
    )
    def search_gmail_messages(
        query: str,
    ) -> list[dict]:
        """Search and read the authenticated user's Gmail messages.

        Use this tool when the user asks about email that currently
        exists in their connected Gmail account. It may read message
        sender, subject, and body content but does not modify Gmail.
        """

        gmail = build_gmail_client(
            db=db,
            user_id=user_id,
        )

        result = (
            gmail.users()
            .messages()
            .list(
                userId="me",
                q=query,
                maxResults=5,
            )
            .execute()
        )

        message_refs = result.get(
            "messages",
            [],
        )

        messages: list[dict] = []

        for message_ref in message_refs:
            message_id = message_ref.get("id")

            if not isinstance(
                message_id,
                str,
            ):
                continue

            raw_message = (
                gmail.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="full",
                )
                .execute()
            )

            message = normalize_gmail_message(
                raw_message
            )

            messages.append(
                {
                    "message_id":
                        message.provider_message_id,
                    "thread_id":
                        message.provider_thread_id,
                    "sender":
                        message.sender,
                    "subject":
                        message.subject,
                    "body":
                        message.body_text,
                }
            )

        return messages

    @tool(
        "create_gmail_draft",
        args_schema=CreateGmailDraftArgs,
    )
    def create_gmail_draft_tool(
        recipient: str,
        subject: str,
        body: str,
    ) -> dict:
        """Create a draft in the authenticated user's Gmail account.

        Use this only when the user explicitly asks FlowPilot to
        create or prepare a Gmail draft. This creates a draft only;
        it does not send the email.
        """

        message = EmailMessage()
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        result = create_gmail_draft(
            db=db,
            user_id=user_id,
            message=message,
        )

        return {
            "draft_id": result.get("id"),
            "message_id": (
                result.get(
                    "message",
                    {},
                ).get("id")
            ),
            "status": "draft_created",
        }

    return [
        search_gmail_messages,
        create_gmail_draft_tool,
    ]
