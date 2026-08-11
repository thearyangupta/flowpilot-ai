"""add pgvector extension

Revision ID: 3596c01dfe4c
Revises: fbbe9329ef95
Create Date: 2026-08-11 12:42:31.588555

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3596c01dfe4c'
down_revision: Union[str, Sequence[str], None] = 'fbbe9329ef95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS vector")