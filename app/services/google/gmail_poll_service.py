from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.google.google_provider_service import (
    build_gmail_client,
)


DEFAULT_GMAIL_PAGE_SIZE = 50
MAX_GMAIL_PAGE_SIZE = 500


class GmailPollError(Exception):
    """Base exception for Gmail polling failures."""


class InvalidGmailPollQueryError(GmailPollError):
    """Raised when a Gmail polling query is empty."""


class InvalidGmailPageSizeError(GmailPollError):
    """Raised when the requested Gmail page size is invalid."""


class GmailMessageListError(GmailPollError):
    """Raised when Gmail message discovery fails."""


class GmailMessageRetrievalError(GmailPollError):
    """Raised when a Gmail message cannot be retrieved."""


@dataclass(frozen=True)
class GmailMessageReference:
    provider_message_id: str
    provider_thread_id: str | None


@dataclass(frozen=True)
class GmailMessagePage:
    messages: tuple[GmailMessageReference, ...]
    next_page_token: str | None

@dataclass(frozen=True)
class GmailHistoryMessage:
    provider_message_id: str
    provider_thread_id: str | None


@dataclass(frozen=True)
class GmailHistoryPage:
    messages: tuple[GmailHistoryMessage, ...]
    next_page_token: str | None
    history_id: str | None


def list_gmail_messages(
    db: Session,
    *,
    user_id: UUID,
    query: str,
    page_token: str | None = None,
    max_results: int = DEFAULT_GMAIL_PAGE_SIZE,
) -> GmailMessagePage:
    normalized_query = query.strip()

    if not normalized_query:
        raise InvalidGmailPollQueryError(
            "A Gmail search query is required."
        )

    if not 1 <= max_results <= MAX_GMAIL_PAGE_SIZE:
        raise InvalidGmailPageSizeError(
            f"max_results must be between 1 and "
            f"{MAX_GMAIL_PAGE_SIZE}."
        )

    gmail = build_gmail_client(
        db=db,
        user_id=user_id,
    )

    try:
        response: dict[str, Any] = (
            gmail.users()
            .messages()
            .list(
                userId="me",
                q=normalized_query,
                maxResults=max_results,
                pageToken=page_token,
            )
            .execute()
        )

    except Exception as error:
        raise GmailMessageListError(
            "Gmail messages could not be listed."
        ) from error

    message_references = tuple(
        GmailMessageReference(
            provider_message_id=item["id"],
            provider_thread_id=item.get("threadId"),
        )
        for item in response.get("messages", [])
        if item.get("id")
    )

    return GmailMessagePage(
        messages=message_references,
        next_page_token=response.get("nextPageToken"),
    )



def get_gmail_message(
    db: Session,
    *,
    user_id: UUID,
    provider_message_id: str,
) -> dict[str, Any]:
    """
    Retrieve one complete Gmail message.

    Returns the raw Gmail API payload.
    """

    if not provider_message_id.strip():
        raise GmailMessageRetrievalError(
            "Provider message id is required."
        )

    gmail = build_gmail_client(
        db=db,
        user_id=user_id,
    )

    try:
        payload: dict[str, Any] = (
            gmail.users()
            .messages()
            .get(
                userId="me",
                id=provider_message_id,
                format="full",
            )
            .execute()
        )

    except Exception as error:
        raise GmailMessageRetrievalError(
            "Gmail message could not be retrieved."
        ) from error

    return payload


def poll_selected_messages(
    db: Session,
    *,
    user_id: UUID,
    query: str,
) -> tuple[GmailMessageReference, ...]:
    """
    Poll every page of Gmail search results.

    Returns all matching message references.
    """

    collected: list[GmailMessageReference] = []

    page_token: str | None = None

    while True:
        page = list_gmail_messages(
            db=db,
            user_id=user_id,
            query=query,
            page_token=page_token,
        )

        collected.extend(page.messages)

        if page.next_page_token is None:
            break

        page_token = page.next_page_token

    return tuple(collected)


def list_gmail_history(
    db: Session,
    *,
    user_id: UUID,
    start_history_id: str,
    page_token: str | None = None,
) -> GmailHistoryPage:
    if not start_history_id.strip():
        raise GmailPollError(
            "A Gmail history id is required."
        )

    gmail = build_gmail_client(
        db=db,
        user_id=user_id,
    )

    try:
        response: dict[str, Any] = (
            gmail.users()
            .history()
            .list(
                userId="me",
                startHistoryId=start_history_id,
                pageToken=page_token,
                historyTypes=["messageAdded"],
            )
            .execute()
        )

    except Exception as error:
        raise GmailMessageListError(
            "Gmail history could not be listed."
        ) from error

    collected: list[GmailHistoryMessage] = []

    for history_record in response.get("history", []):
        for added in history_record.get(
            "messagesAdded",
            [],
        ):
            message = added.get("message", {})

            provider_message_id = message.get("id")

            if not provider_message_id:
                continue

            collected.append(
                GmailHistoryMessage(
                    provider_message_id=provider_message_id,
                    provider_thread_id=message.get("threadId"),
                )
            )

    return GmailHistoryPage(
        messages=tuple(collected),
        next_page_token=response.get("nextPageToken"),
        history_id=response.get("historyId"),
    )


def poll_gmail_history(
    db: Session,
    *,
    user_id: UUID,
    start_history_id: str,
) -> tuple[GmailHistoryMessage, ...]:
    collected: list[GmailHistoryMessage] = []

    page_token: str | None = None

    while True:
        page = list_gmail_history(
            db=db,
            user_id=user_id,
            start_history_id=start_history_id,
            page_token=page_token,
        )

        collected.extend(page.messages)

        if page.next_page_token is None:
            break

        page_token = page.next_page_token

    return tuple(collected)