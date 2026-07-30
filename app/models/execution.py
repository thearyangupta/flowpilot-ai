from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Enum as SQLEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.models.enums import ExecutionStatus

if TYPE_CHECKING:
    from app.models.workflow import Workflow
    from app.models.step_run import StepRun
    from app.models.execution_event import ExecutionEvent

class Execution(TimestampMixin, Base):
    __tablename__ = "executions"

    __table_args__ = (
    UniqueConstraint(
        "workflow_id",
        "idempotency_key",
        name="uq_executions_workflow_id_idempotency_key",
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

    status: Mapped[ExecutionStatus] = mapped_column(
        SQLEnum(
            ExecutionStatus,
            name="execution_status",
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ),
        nullable=False,
        default=ExecutionStatus.PENDING,
    )

    workflow: Mapped["Workflow"] = relationship(
        back_populates="executions",
    )
    step_runs: Mapped[list["StepRun"]] = relationship(
    back_populates="execution",
    cascade="all, delete-orphan",
    passive_deletes=True,
    )

    events: Mapped[list["ExecutionEvent"]] = relationship(
    back_populates="execution",
    cascade="all, delete-orphan",
    passive_deletes=True,
)

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
)

    input_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
)

    input_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
)