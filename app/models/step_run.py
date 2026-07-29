from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Enum as SQLEnum, ForeignKey, Text,String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime
from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.models.enums import StepRunStatus

if TYPE_CHECKING:
    from app.models.execution import Execution
    from app.models.workflow_step import WorkflowStep


class StepRun(TimestampMixin, Base):
    __tablename__ = "step_runs"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    execution_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "executions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    workflow_step_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "workflow_steps.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[StepRunStatus] = mapped_column(
        SQLEnum(
            StepRunStatus,
            name="step_run_status",
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ),
        nullable=False,
        default=StepRunStatus.PENDING,
    )

    input_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    output_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    execution: Mapped["Execution"] = relationship(
        back_populates="step_runs",
    )

    workflow_step: Mapped["WorkflowStep"] = relationship(
        back_populates="step_runs",
    )

    started_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    finished_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    error_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )