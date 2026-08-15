import hashlib
import json
from copy import deepcopy
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reply_draft_revision import ReplyDraftRevision


class ReplyDraftRevisionError(Exception):
    """Base exception for reply-draft revision failures."""


class ReplyDraftRevisionNotFoundError(ReplyDraftRevisionError):
    """Raised when an owned revision cannot be found."""


def canonicalize_content(
    content: dict[str, Any],
) -> bytes:
    """
    Produce one deterministic byte representation for JSON content.

    Sorting keys prevents semantically identical dictionaries from
    producing different hashes only because their key order differs.
    """
    try:
        serialized = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ReplyDraftRevisionError(
            "Reply draft content is not valid canonical JSON."
        ) from error

    return serialized.encode("utf-8")


def hash_content(
    content: dict[str, Any],
) -> str:
    return hashlib.sha256(
        canonicalize_content(content)
    ).hexdigest()


def create_revision_record(
    db: Session,
    *,
    reply_draft_id: UUID,
    user_id: UUID,
    revision_number: int,
    content: dict[str, Any],
    created_by_actor: str,
    created_by_user_id: UUID | None,
) -> ReplyDraftRevision:
    revision = ReplyDraftRevision(
        reply_draft_id=reply_draft_id,
        user_id=user_id,
        revision_number=revision_number,
        content=deepcopy(content),
        content_hash=hash_content(content),
        created_by_actor=created_by_actor,
        created_by_user_id=created_by_user_id,
    )

    db.add(revision)
    db.flush()

    return revision


def get_revision_for_user(
    db: Session,
    *,
    reply_draft_id: UUID,
    user_id: UUID,
    revision_number: int,
) -> ReplyDraftRevision:
    revision = db.execute(
        select(ReplyDraftRevision).where(
            ReplyDraftRevision.reply_draft_id
            == reply_draft_id,
            ReplyDraftRevision.user_id == user_id,
            ReplyDraftRevision.revision_number
            == revision_number,
        )
    ).scalar_one_or_none()

    if revision is None:
        raise ReplyDraftRevisionNotFoundError(
            "Reply draft revision not found."
        )

    return revision
