from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime,ForeignKey, LargeBinary, String,UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class OAuthConnection(TimestampMixin, Base):
    __tablename__ = "oauth_connections"

    __table_args__ = (
    UniqueConstraint(
        "provider",
        "provider_subject",
        name="uq_oauth_connections_provider_subject",
    ),
)

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    provider_subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    access_token_ciphertext: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
    )

    refresh_token_ciphertext: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
    )

    scopes: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="oauth_connections",
    )

    gmail_history_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
)

    gmail_watch_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
)