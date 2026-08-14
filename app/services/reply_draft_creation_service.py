from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.providers.gemini import GeminiGroundedReplyProvider
from app.services.google.gmail_draft_service import (
    build_reply_message,
    create_gmail_draft,
)
from app.services.knowledge.context_service import (
    build_knowledge_context,
    label_context_hits,
    select_context_hits,
)
from app.services.knowledge.embedding_provider import Embedder
from app.services.knowledge.grounded_reply_service import (
    GroundedReplyStatus,
    evaluate_grounded_reply,
)
from app.services.knowledge.retrieval_service import hybrid_search
from app.services.reply_draft_service import create_pending


class ReplyDraftCreationError(Exception):
    """Raised when a pending reply draft cannot be created."""


def create_grounded_pending_reply(
    *,
    db: Session,
    user_id: UUID,
    embedder: Embedder,
    reply_provider: GeminiGroundedReplyProvider,
    source_message: dict[str, Any],
    max_context_tokens: int = 3000,
) -> dict[str, Any]:
    sender = str(
        source_message.get("sender")
        or source_message.get("from")
        or ""
    ).strip()

    subject = str(
        source_message.get("subject")
        or ""
    ).strip()

    body_text = str(
        source_message.get("body_text")
        or source_message.get("body")
        or ""
    ).strip()

    message_id = str(
        source_message.get("message_id")
        or source_message.get("id")
        or ""
    ).strip()

    references = source_message.get("references")

    if not sender:
        raise ReplyDraftCreationError(
            "Source message sender is required."
        )

    if not body_text:
        raise ReplyDraftCreationError(
            "Source message body is required."
        )

    if not message_id:
        raise ReplyDraftCreationError(
            "Source Gmail message id is required."
        )

    query = "\n".join(
        part
        for part in (subject, body_text)
        if part
    )

    hits = hybrid_search(
        db=db,
        user_id=user_id,
        query=query,
        embedder=embedder,
    )

    selected_hits = select_context_hits(
        hits,
        max_tokens=max_context_tokens,
    )

    sources = label_context_hits(
        selected_hits
    )

    knowledge_context = build_knowledge_context(
        sources
    )

    if not sources:
        return {
            "status": "needs_knowledge",
            "missing_information": [
                "No supporting knowledge was found."
            ],
        }

    generated_reply = reply_provider.generate(
        sender=sender,
        subject=subject,
        body_text=body_text,
        knowledge_context=knowledge_context,
    )

    evaluated = evaluate_grounded_reply(
        reply=generated_reply,
        sources=sources,
    )

    if (
        evaluated.status
        == GroundedReplyStatus.NEEDS_KNOWLEDGE
        or evaluated.reply is None
    ):
        return {
            "status": "needs_knowledge",
            "missing_information": list(
                evaluated.missing_information
            ),
        }

    reply = evaluated.reply

    gmail_message = build_reply_message(
        recipient=sender,
        subject=reply.subject,
        body=reply.body,
        in_reply_to=message_id,
        references=(
            str(references)
            if references
            else None
        ),
    )

    gmail_draft = create_gmail_draft(
        db,
        user_id=user_id,
        message=gmail_message,
    )

    gmail_draft_id = str(
        gmail_draft.get("id")
        or ""
    ).strip()

    if not gmail_draft_id:
        raise ReplyDraftCreationError(
            "Gmail did not return a draft id."
        )

    draft_message = {
        "recipient": sender,
        "subject": reply.subject,
        "body": reply.body,
        "citation_ids": list(
            reply.citation_ids
        ),
    }

    pending_draft = create_pending(
        db,
        user_id=user_id,
        gmail_draft_id=gmail_draft_id,
        source_message=source_message,
        draft_message=draft_message,
    )

    return {
        "status": "pending_approval",
        "reply_draft_id": str(
            pending_draft.id
        ),
        "gmail_draft_id": gmail_draft_id,
        "citation_ids": list(
            reply.citation_ids
        ),
    }
