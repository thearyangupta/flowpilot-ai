from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, LargeBinary, String, UniqueConstraint,ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.db.mixins import TimestampMixin


class OAuthAttempt(TimestampMixin, Base):
    __tablename__ = "oauth_attempts"

    __table_args__ = (
        UniqueConstraint(
            "state_hash",
            name="uq_oauth_attempts_state_hash",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    purpose: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    requested_scopes: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    state_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    verifier_ciphertext: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )