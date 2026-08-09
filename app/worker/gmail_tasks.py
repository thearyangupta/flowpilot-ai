from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.oauth_connection import OAuthConnection
from app.services.google.gmail_message_service import (
    normalize_gmail_message,
)
from app.services.google.gmail_poll_service import (
    get_gmail_message,
    poll_selected_messages,
)
from app.services.google.gmail_trigger_service import (
    GmailTriggerPayload,
    trigger_email_workflow,
)
from app.services.google.gmail_ingestion_service import (
    ingest_gmail_message,
)
from app.worker.celery_app import celery_app


@celery_app.task(
    name="flowpilot.gmail.poll_connected_accounts",
)
def poll_connected_accounts() -> None:
    settings = get_settings()
    query = settings.gmail_poll_query

    db = SessionLocal()

    try:
        connections = db.scalars(
            select(OAuthConnection).where(
                OAuthConnection.provider == "google",
            )
        ).all()

        for connection in connections:
            user_id = connection.user_id

            message_references = poll_selected_messages(
                db=db,
                user_id=user_id,
                query=query,
            )

            for message_reference in message_references:
                raw_message = get_gmail_message(
                    db=db,
                    user_id=user_id,
                    provider_message_id=message_reference.provider_message_id,
                )

                message = normalize_gmail_message(raw_message)

                ingestion = ingest_gmail_message(
                    db=db,
                    user_id=user_id,
                    provider_message_id=message.provider_message_id,
                    provider_thread_id=message.provider_thread_id,
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
                    workflow_id=connection.workflow_id,
                    provider_message_id=message.provider_message_id,
                    sender=message.sender,
                    subject=message.subject,
                    body_text=message.body_text,
                )

                trigger_email_workflow(
                    db=db,
                    payload=payload,
                )

                db.commit()

    finally:
        db.close()