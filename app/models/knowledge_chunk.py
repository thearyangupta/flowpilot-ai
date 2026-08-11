from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin
from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed

if TYPE_CHECKING:
    from app.models.knowledge_document import KnowledgeDocument


class KnowledgeChunk(TimestampMixin, Base):
    __tablename__ = "knowledge_chunks"

    __table_args__ = (
        UniqueConstraint("document_id", "ordinal"),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "knowledge_documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    user_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )

    ordinal: Mapped[int] = mapped_column(
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    token_count: Mapped[int] = mapped_column(
        nullable=False,
    )
    
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True,
    )
    search_vector: Mapped[str | None] = mapped_column(
        Computed(
            "to_tsvector('english', content)",
            persisted=True,
        ),
        nullable=True,
)

    document: Mapped["KnowledgeDocument"] = relationship(
        back_populates="chunks",
    )