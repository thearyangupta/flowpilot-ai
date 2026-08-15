from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReplyDraftRevision(Base):
    __tablename__ = "reply_draft_revisions"

    __table_args__ = (
        UniqueConstraint(
            "reply_draft_id",
            "revision_number",
            name="uq_reply_draft_revisions_draft_revision",
        ),
        Index(
            "ix_reply_draft_revisions_user_draft",
            "user_id",
            "reply_draft_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    reply_draft_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "reply_drafts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    revision_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    created_by_actor: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    created_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
