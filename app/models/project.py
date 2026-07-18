from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.workflow import Workflow


class Project(TimestampMixin, Base):#This line causes SQLAlchemy to treat Project as an ORM model.
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    workflows: Mapped[list["Workflow"]] = relationship(
    back_populates="project",
    cascade="all, delete-orphan",
)