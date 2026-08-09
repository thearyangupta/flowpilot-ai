from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.execution import Execution
    from app.models.project import Project
    from app.models.workflow_step import WorkflowStep
    from app.models.oauth_connection import OAuthConnection

class Workflow(TimestampMixin, Base):
    __tablename__ = "workflows"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    project: Mapped["Project"] = relationship(
        back_populates="workflows",
    )

    executions: Mapped[list["Execution"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
    )

    steps: Mapped[list["WorkflowStep"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="WorkflowStep.position",
    )

    oauth_connections: Mapped[list["OAuthConnection"]] = relationship(
        back_populates="workflow",
)