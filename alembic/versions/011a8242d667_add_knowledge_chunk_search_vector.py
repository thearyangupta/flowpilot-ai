"""add knowledge chunk search vector

Revision ID: 011a8242d667
Revises: 57067e5492bf
Create Date: 2026-08-11 13:57:05.303808

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '011a8242d667'
down_revision: Union[str, Sequence[str], None] = '57067e5492bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "knowledge_chunks",
        sa.Column(
            "search_vector",
            sa.String(),
            sa.Computed(
                "to_tsvector('english', content)",
                persisted=True,
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column(
        "knowledge_chunks",
        "search_vector",
    )