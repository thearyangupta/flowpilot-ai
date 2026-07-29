"""add step run lifecycle fields

Revision ID: 0c06a8f877b9
Revises: 95f01d13255e
Create Date: 2026-07-29 14:35:15.623204
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0c06a8f877b9"
down_revision: Union[str, Sequence[str], None] = "95f01d13255e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Alembic does not automatically detect new PostgreSQL enum values.
    op.execute(
        "ALTER TYPE step_run_status "
        "ADD VALUE IF NOT EXISTS 'pending'"
    )
    op.execute(
        "ALTER TYPE step_run_status "
        "ADD VALUE IF NOT EXISTS 'retry_wait'"
    )

    op.add_column(
        "step_runs",
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "step_runs",
        sa.Column(
            "finished_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Temporary server default protects existing rows.
    op.add_column(
        "step_runs",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "step_runs",
        sa.Column(
            "error_type",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "step_runs",
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
    )

    op.drop_column(
        "step_runs",
        "error",
    )

    # Application code controls the default after migration.
    op.alter_column(
        "step_runs",
        "attempt_count",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.add_column(
        "step_runs",
        sa.Column(
            "error",
            sa.Text(),
            nullable=True,
        ),
    )

    # Preserve available failure information before dropping the new columns.
    op.execute(
        """
        UPDATE step_runs
        SET error = CASE
            WHEN error_type IS NOT NULL
                 AND error_message IS NOT NULL
                THEN error_type || ': ' || error_message
            WHEN error_message IS NOT NULL
                THEN error_message
            WHEN error_type IS NOT NULL
                THEN error_type
            ELSE NULL
        END
        """
    )

    op.drop_column(
        "step_runs",
        "error_message",
    )

    op.drop_column(
        "step_runs",
        "error_type",
    )

    op.drop_column(
        "step_runs",
        "attempt_count",
    )

    op.drop_column(
        "step_runs",
        "finished_at",
    )

    op.drop_column(
        "step_runs",
        "started_at",
    )

    # PostgreSQL enum values are intentionally retained.