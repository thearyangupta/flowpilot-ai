"""add queued execution status

Revision ID: 0cf11ca2519f
Revises: aed91862ebaa
Create Date: 2026-07-31 14:07:41.587811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0cf11ca2519f'
down_revision: Union[str, Sequence[str], None] = 'aed91862ebaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE execution_status ADD VALUE IF NOT EXISTS 'queued'"
    )


def downgrade() -> None:
    pass