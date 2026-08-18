from dataclasses import dataclass
from typing import Any
from uuid import UUID

from googleapiclient.errors import HttpError
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


class GmailMessageNotFoundError(
    GmailMessageRetrievalError
):
    """
    Raised when a Gmail history message no longer exists.

    Gmail history may reference a message that is deleted or
    otherwise unavailable before FlowPilot retrieves it.
    """


class GmailHistoryCursorError(GmailPollError):
    """Raised when Gmail cannot provide a valid history cursor."""


class GmailHistoryExpiredError(GmailPollError):
    """Raised when the saved Gmail history cursor is no longer valid."""


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


@dataclass(frozen=True)
class GmailHistoryPollResult:
    messages: tuple[GmailHistoryMessage, ...]
    history_id: str


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
        next_page_token=response.get(
            "nextPageToken"
        ),
    )


def get_gmail_history_cursor(
    db: Session,
    *,
    user_id: UUID,
) -> str:
    """
    Return Gmail's current mailbox history cursor.

    This is used as the baseline when Gmail is connected so
    existing mailbox messages are not treated as new events.
    """

    gmail = build_gmail_client(
        db=db,
        user_id=user_id,
    )

    try:
        response: dict[str, Any] = (
            gmail.users()
            .getProfile(
                userId="me",
            )
            .execute()
        )

    except Exception as error:
        raise GmailHistoryCursorError(
            "Gmail history cursor could not be retrieved."
        ) from error

    history_id = str(
        response.get("historyId") or ""
    ).strip()

    if not history_id:
        raise GmailHistoryCursorError(
            "Gmail did not return a history cursor."
        )

    return history_id


def get_gmail_message(
    db: Session,
    *,
    user_id: UUID,
    provider_message_id: str,
) -> dict[str, Any]:
    """
    Retrieve one complete Gmail message.

    Returns the raw Gmail API payload.

    A Gmail history record may reference a message that no
    longer exists by the time FlowPilot retrieves it. That
    specific 404 case is exposed separately so the worker can
    safely skip only that message and continue processing the
    rest of the mailbox history.
    """

    normalized_message_id = (
        provider_message_id.strip()
    )

    if not normalized_message_id:
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
                id=normalized_message_id,
                format="full",
            )
            .execute()
        )

    except HttpError as error:
        status = getattr(
            getattr(
                error,
                "resp",
                None,
            ),
            "status",
            None,
        )

        if status == 404:
            raise GmailMessageNotFoundError(
                "Gmail message no longer exists."
            ) from error

        raise GmailMessageRetrievalError(
            "Gmail message could not be retrieved."
        ) from error

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
    Legacy/developer query polling.

    Kept for reconciliation and explicit diagnostic searches.
    Production Gmail automation uses Gmail history polling.
    """

    collected: list[
        GmailMessageReference
    ] = []

    page_token: str | None = None

    while True:
        page = list_gmail_messages(
            db=db,
            user_id=user_id,
            query=query,
            page_token=page_token,
        )

        collected.extend(
            page.messages
        )

        if page.next_page_token is None:
            break

        page_token = (
            page.next_page_token
        )

    return tuple(
        collected
    )


def list_gmail_history(
    db: Session,
    *,
    user_id: UUID,
    start_history_id: str,
    page_token: str | None = None,
) -> GmailHistoryPage:
    normalized_history_id = (
        start_history_id.strip()
    )

    if not normalized_history_id:
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
                startHistoryId=(
                    normalized_history_id
                ),
                pageToken=page_token,
                historyTypes=[
                    "messageAdded"
                ],
            )
            .execute()
        )

    except HttpError as error:
        status = getattr(
            getattr(
                error,
                "resp",
                None,
            ),
            "status",
            None,
        )

        if status == 404:
            raise GmailHistoryExpiredError(
                (
                    "Saved Gmail history cursor "
                    "is no longer valid."
                )
            ) from error

        raise GmailMessageListError(
            "Gmail history could not be listed."
        ) from error

    except Exception as error:
        raise GmailMessageListError(
            "Gmail history could not be listed."
        ) from error

    collected: list[
        GmailHistoryMessage
    ] = []

    for history_record in response.get(
        "history",
        [],
    ):
        for added in history_record.get(
            "messagesAdded",
            [],
        ):
            message = added.get(
                "message",
                {},
            )

            provider_message_id = (
                message.get(
                    "id"
                )
            )

            if not provider_message_id:
                continue

            collected.append(
                GmailHistoryMessage(
                    provider_message_id=(
                        provider_message_id
                    ),
                    provider_thread_id=(
                        message.get(
                            "threadId"
                        )
                    ),
                )
            )

    history_id_raw = response.get(
        "historyId"
    )

    history_id = (
        str(
            history_id_raw
        )
        if history_id_raw is not None
        else None
    )

    return GmailHistoryPage(
        messages=tuple(
            collected
        ),
        next_page_token=(
            response.get(
                "nextPageToken"
            )
        ),
        history_id=history_id,
    )


def poll_gmail_history(
    db: Session,
    *,
    user_id: UUID,
    start_history_id: str,
) -> GmailHistoryPollResult:
    """
    Return all Gmail messages added after start_history_id
    together with the latest history cursor.

    Duplicate message IDs are removed because Gmail history
    may mention the same message in multiple history records.
    """

    normalized_history_id = (
        start_history_id.strip()
    )

    if not normalized_history_id:
        raise GmailPollError(
            "A Gmail history id is required."
        )

    collected: list[
        GmailHistoryMessage
    ] = []

    seen_message_ids: set[
        str
    ] = set()

    page_token: str | None = None

    latest_history_id = (
        normalized_history_id
    )

    while True:
        page = list_gmail_history(
            db=db,
            user_id=user_id,
            start_history_id=(
                normalized_history_id
            ),
            page_token=page_token,
        )

        if page.history_id:
            latest_history_id = (
                page.history_id
            )

        for message in page.messages:
            if (
                message.provider_message_id
                in seen_message_ids
            ):
                continue

            seen_message_ids.add(
                message.provider_message_id
            )

            collected.append(
                message
            )

        if page.next_page_token is None:
            break

        page_token = (
            page.next_page_token
        )

    return GmailHistoryPollResult(
        messages=tuple(
            collected
        ),
        history_id=latest_history_id,
    )