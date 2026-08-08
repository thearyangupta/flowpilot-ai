from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.models.enums import ReplyDraftStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.reply_draft_audit_event import ReplyDraftAuditEvent


class ReplyDraft(TimestampMixin, Base):
    __tablename__ = "reply_drafts"

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

    gmail_draft_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[ReplyDraftStatus] = mapped_column(
        String(32),
        nullable=False,
        default=ReplyDraftStatus.PENDING_APPROVAL,
    )

    approved_by: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    source_message: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    draft_message: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    user: Mapped["User"] = relationship(
        foreign_keys=[user_id],
    )

    approver: Mapped["User | None"] = relationship(
        foreign_keys=[approved_by],
    )

    gmail_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
)
    audit_events: Mapped[list["ReplyDraftAuditEvent"]] = relationship(
        back_populates="reply_draft",
        cascade="all, delete-orphan",
)