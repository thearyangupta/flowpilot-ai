from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Computed,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR
from app.db.base import Base
from app.db.mixins import TimestampMixin
from pgvector.sqlalchemy import Vector

if TYPE_CHECKING:
    from app.models.knowledge_document import KnowledgeDocument


class KnowledgeChunk(TimestampMixin, Base):
    __tablename__ = "knowledge_chunks"

    __table_args__ = (
        UniqueConstraint("document_id", "ordinal"),
        Index(
            "ix_knowledge_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={
                "embedding": "vector_cosine_ops",
            },
        ),
        Index(
            "ix_knowledge_chunks_search_vector_gin",
            "search_vector",
            postgresql_using="gin",
        ),
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

    token_start: Mapped[int] = mapped_column(
        nullable=False,
    )

    token_end: Mapped[int] = mapped_column(
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    token_count: Mapped[int] = mapped_column(
        nullable=False,
    )

    chunk_version: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True,
    )

    embedding_model: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    embedding_key: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', content)",
            persisted=True,
        ),
        nullable=True,
    )

    document: Mapped["KnowledgeDocument"] = relationship(
        back_populates="chunks",
    )