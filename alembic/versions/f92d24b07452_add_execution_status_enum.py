"""add execution status enum

Revision ID: f92d24b07452
Revises: 0054ae968049
Create Date: 2026-07-20 17:46:47.476106
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f92d24b07452"
down_revision: Union[str, Sequence[str], None] = "0054ae968049"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


execution_status_enum = postgresql.ENUM(
    "pending",
    "running",
    "succeeded",
    "failed",
    "cancelled",
    name="execution_status",
    create_type=False,
)


def upgrade() -> None:
    execution_status_enum.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.alter_column(
        "executions",
        "status",
        existing_type=sa.String(length=50),
        type_=execution_status_enum,
        existing_nullable=False,
        postgresql_using="status::execution_status",
    )


def downgrade() -> None:
    op.alter_column(
        "executions",
        "status",
        existing_type=execution_status_enum,
        type_=sa.String(length=50),
        existing_nullable=False,
        postgresql_using="status::text",
    )

    execution_status_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )