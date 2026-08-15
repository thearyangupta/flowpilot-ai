from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApprovalDecision(Base):
    __tablename__ = "approval_decisions"

    __table_args__ = (
        Index(
            "ix_approval_decisions_user_revision",
            "user_id",
            "revision_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    revision_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "reply_draft_revisions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
