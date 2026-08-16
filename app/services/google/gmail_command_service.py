import hashlib
import json
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.gmail_command import GmailCommand


STATE_IN_PROGRESS = "in_progress"
STATE_COMPLETED = "completed"
STATE_UNCERTAIN = "uncertain"


class GmailCommandError(Exception):
    pass


class GmailCommandConflictError(
    GmailCommandError
):
    pass


class GmailCommandInProgressError(
    GmailCommandError
):
    pass


class GmailCommandOutcomeUncertainError(
    GmailCommandError
):
    pass


def resolve_idempotency_key(
    *,
    provided_key: str | None,
    draft_id: UUID,
    revision_number: int,
) -> str:
    if provided_key is not None:
        cleaned = provided_key.strip()

        if cleaned:
            return cleaned

    return (
        f"reply-draft:{draft_id}:"
        f"revision:{revision_number}:send"
    )


def build_send_fingerprint(
    *,
    draft_id: UUID,
    revision_number: int,
    gmail_draft_id: str,
    content_hash: str,
) -> str:
    payload = {
        "operation":
            "gmail.send_draft",
        "draft_id":
            str(draft_id),
        "revision_number":
            revision_number,
        "gmail_draft_id":
            gmail_draft_id,
        "content_hash":
            content_hash,
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(
        canonical
    ).hexdigest()


def _classify_existing(
    *,
    command: GmailCommand,
    fingerprint: str,
) -> tuple[GmailCommand, bool]:
    if command.fingerprint != fingerprint:
        raise GmailCommandConflictError(
            "Idempotency key fingerprint mismatch."
        )

    if command.state == STATE_COMPLETED:
        return command, True

    if command.state == STATE_UNCERTAIN:
        raise (
            GmailCommandOutcomeUncertainError(
                "Previous Gmail outcome is uncertain."
            )
        )

    raise GmailCommandInProgressError(
        "Gmail command is already in progress."
    )


def claim_or_replay(
    db: Session,
    *,
    user_id: UUID,
    reply_draft_id: UUID,
    revision_number: int,
    idempotency_key: str,
    fingerprint: str,
) -> tuple[GmailCommand, bool]:
    existing = db.scalar(
        select(GmailCommand)
        .where(
            GmailCommand.user_id == user_id,
            GmailCommand.idempotency_key
            == idempotency_key,
        )
        .with_for_update()
    )

    if existing is not None:
        return _classify_existing(
            command=existing,
            fingerprint=fingerprint,
        )

    command = GmailCommand(
        user_id=user_id,
        reply_draft_id=reply_draft_id,
        revision_number=revision_number,
        idempotency_key=idempotency_key,
        fingerprint=fingerprint,
        state=STATE_IN_PROGRESS,
        outcome=None,
    )

    try:
        with db.begin_nested():
            db.add(command)
            db.flush()

    except IntegrityError:
        existing = db.scalar(
            select(GmailCommand)
            .where(
                GmailCommand.user_id
                == user_id,
                GmailCommand.idempotency_key
                == idempotency_key,
            )
            .with_for_update()
        )

        if existing is None:
            raise

        return _classify_existing(
            command=existing,
            fingerprint=fingerprint,
        )

    return command, False


def mark_completed(
    *,
    command: GmailCommand,
    outcome: dict[str, Any],
) -> None:
    command.state = STATE_COMPLETED
    command.outcome = outcome


def mark_uncertain(
    *,
    command: GmailCommand,
    outcome: dict[str, Any],
) -> None:
    command.state = STATE_UNCERTAIN
    command.outcome = outcome