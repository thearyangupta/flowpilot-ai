from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, LargeBinary, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

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