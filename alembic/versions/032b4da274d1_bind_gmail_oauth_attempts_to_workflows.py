"""bind gmail oauth attempts to workflows

Revision ID: 032b4da274d1
Revises: 0df91a709e4a
Create Date: 2026-08-18 15:50:54.059722

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '032b4da274d1'
down_revision: Union[str, Sequence[str], None] = '0df91a709e4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "oauth_attempts",
        sa.Column(
            "workflow_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_oauth_attempts_workflow_id",
        "oauth_attempts",
        "workflows",
        ["workflow_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_oauth_attempts_workflow_id",
        "oauth_attempts",
        ["workflow_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_oauth_attempts_workflow_id",
        table_name="oauth_attempts",
    )

    op.drop_constraint(
        "fk_oauth_attempts_workflow_id",
        "oauth_attempts",
        type_="foreignkey",
    )

    op.drop_column(
        "oauth_attempts",
        "workflow_id",
    )
