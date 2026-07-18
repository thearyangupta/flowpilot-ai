from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.workflow import Workflow


class Execution(TimestampMixin, Base):
    __tablename__ = "executions"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    workflow_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflows.id",ondelete="CASCADE"),
        nullable=False,
        index= True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    workflow: Mapped["Workflow"] = relationship(
        back_populates="executions",
    )