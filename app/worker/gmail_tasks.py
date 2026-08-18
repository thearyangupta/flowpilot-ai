from __future__ import annotations

import logging

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.oauth_connection import (
    OAuthConnection,
)
from app.services.auth.oauth_token_service import (
    MissingGoogleScopes,
)
from app.services.google.gmail_cursor_service import (
    save_gmail_history_cursor,
)
from app.services.google.gmail_ingestion_service import (
    ingest_gmail_message,
)
from app.services.google.gmail_message_service import (
    normalize_gmail_message,
)
from app.services.google.gmail_poll_service import (
    GmailHistoryExpiredError,
    get_gmail_history_cursor,
    get_gmail_message,
    poll_gmail_history,
)
from app.services.google.gmail_trigger_service import (
    GmailTriggerPayload,
    trigger_email_workflow,
)
from app.worker.celery_app import celery_app


logger = logging.getLogger(__name__)


def _initialize_history_cursor(
    *,
    db,
    connection: OAuthConnection,
) -> None:
    history_id = get_gmail_history_cursor(
        db=db,
        user_id=connection.user_id,
    )

    save_gmail_history_cursor(
        db=db,
        connection=connection,
        history_id=history_id,
    )

    db.commit()


@celery_app.task(
    name="flowpilot.gmail.poll_connected_accounts",
)
def poll_connected_accounts() -> None:
    db = SessionLocal()

    try:
        connections = db.scalars(
            select(OAuthConnection).where(
                OAuthConnection.provider
                == "google",
            )
        ).all()

        for connection in connections:
            user_id = connection.user_id

            try:
                if not connection.gmail_history_id:
                    _initialize_history_cursor(
                        db=db,
                        connection=connection,
                    )

                    logger.info(
                        (
                            "Initialized Gmail history "
                            "cursor for connection %s."
                        ),
                        connection.id,
                    )

                    continue

                try:
                    history = poll_gmail_history(
                        db=db,
                        user_id=user_id,
                        start_history_id=(
                            connection.gmail_history_id
                        ),
                    )

                except GmailHistoryExpiredError:
                    db.rollback()

                    _initialize_history_cursor(
                        db=db,
                        connection=connection,
                    )

                    logger.info(
                        (
                            "Reset expired Gmail history "
                            "cursor for connection %s."
                        ),
                        connection.id,
                    )

                    continue

                for message_reference in (
                    history.messages
                ):
                    raw_message = get_gmail_message(
                        db=db,
                        user_id=user_id,
                        provider_message_id=(
                            message_reference
                            .provider_message_id
                        ),
                    )

                    label_ids = set(
                        raw_message.get(
                            "labelIds",
                            [],
                        )
                    )

                    # Gmail history includes mailbox-wide
                    # message additions. FlowPilot should
                    # automate only incoming Inbox mail.
                    if "INBOX" not in label_ids:
                        continue

                    message = normalize_gmail_message(
                        raw_message
                    )

                    ingestion = ingest_gmail_message(
                        db=db,
                        user_id=user_id,
                        provider_message_id=(
                            message.provider_message_id
                        ),
                        provider_thread_id=(
                            message.provider_thread_id
                        ),
                        sender=message.sender,
                        subject=message.subject,
                        body_text=message.body_text,
                        body_hash=message.body_hash,
                    )

                    if not ingestion.created:
                        continue

                    if connection.workflow_id is None:
                        db.commit()
                        continue

                    payload = GmailTriggerPayload(
                        user_id=user_id,
                        workflow_id=(
                            connection.workflow_id
                        ),
                        provider_message_id=(
                            message.provider_message_id
                        ),
                        sender=message.sender,
                        subject=message.subject,
                        body_text=message.body_text,
                    )

                    trigger_email_workflow(
                        db=db,
                        payload=payload,
                    )

                    db.commit()

                save_gmail_history_cursor(
                    db=db,
                    connection=connection,
                    history_id=history.history_id,
                )

                db.commit()

            except MissingGoogleScopes as error:
                db.rollback()

                logger.info(
                    (
                        "Skipping Google connection "
                        "%s because Gmail scopes "
                        "are unavailable: %s"
                    ),
                    connection.id,
                    error,
                )

                continue

            except Exception:
                db.rollback()

                logger.exception(
                    (
                        "Gmail polling failed for "
                        "Google connection %s."
                    ),
                    connection.id,
                )

                continue

    finally:
        db.close()