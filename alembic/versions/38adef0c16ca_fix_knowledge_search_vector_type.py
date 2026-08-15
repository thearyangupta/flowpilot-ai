"""fix knowledge search vector type

Revision ID: 38adef0c16ca
Revises: 108c64ad2117
Create Date: 2026-08-15 11:13:13.365754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38adef0c16ca'
down_revision: Union[str, Sequence[str], None] = '108c64ad2117'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE knowledge_chunks
        DROP COLUMN search_vector
        """
    )

    op.execute(
        """
        ALTER TABLE knowledge_chunks
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english', content)
        ) STORED
        """
    )

    op.create_index(
        "ix_knowledge_chunks_search_vector_gin",
        "knowledge_chunks",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_knowledge_chunks_search_vector_gin",
        table_name="knowledge_chunks",
    )

    op.execute(
        """
        ALTER TABLE knowledge_chunks
        DROP COLUMN search_vector
        """
    )

    op.execute(
        """
        ALTER TABLE knowledge_chunks
        ADD COLUMN search_vector varchar
        GENERATED ALWAYS AS (
            to_tsvector('english', content)
        ) STORED
        """
    )