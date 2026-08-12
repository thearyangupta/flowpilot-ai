"""add token offsets to knowledge chunks

Revision ID: dec4716250d7
Revises: 86336d10141a
Create Date: 2026-08-12 11:48:27.344239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dec4716250d7'
down_revision: Union[str, Sequence[str], None] = '86336d10141a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "knowledge_chunks",
        sa.Column("token_start", sa.Integer(), nullable=False),
    )
    op.add_column(
        "knowledge_chunks",
        sa.Column("token_end", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("knowledge_chunks", "token_end")
    op.drop_column("knowledge_chunks", "token_start")