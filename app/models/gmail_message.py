from datetime import datetime,timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GmailMessage(Base):
    __tablename__ = "gmail_messages"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "provider_message_id",
            name="uq_gmail_messages_user_provider_message",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    provider_message_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    provider_thread_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    sender: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    subject: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    body_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    body_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
)