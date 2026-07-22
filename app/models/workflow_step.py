from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.workflow import Workflow
    from app.models.step_run import StepRun

class WorkflowStep(TimestampMixin, Base):
    __tablename__ = "workflow_steps"

    __table_args__ = (
        UniqueConstraint(
            "workflow_id",
            "position",
            name="uq_workflow_step_position",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    workflow_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "workflows.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    position: Mapped[int] = mapped_column(
        nullable=False,
    )

    step_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    config: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    workflow: Mapped["Workflow"] = relationship(
        back_populates="steps",
    )
    step_runs: Mapped[list["StepRun"]] = relationship(
    back_populates="workflow_step",
    cascade="all, delete-orphan",
    passive_deletes=True,
)