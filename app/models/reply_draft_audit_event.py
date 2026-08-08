from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.reply_draft import ReplyDraft
    from app.models.user import User


class ReplyDraftAuditEvent(TimestampMixin, Base):
    __tablename__ = "reply_draft_audit_events"

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

    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    actor: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    details: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    reply_draft: Mapped["ReplyDraft"] = relationship(
        back_populates="audit_events",
    )

    actor_user: Mapped["User | None"] = relationship()