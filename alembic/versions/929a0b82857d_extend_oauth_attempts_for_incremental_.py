"""extend oauth attempts for incremental authorization

Revision ID: 929a0b82857d
Revises: 0aab559cea97
Create Date: 2026-08-05 12:48:20.680235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '929a0b82857d'
down_revision: Union[str, Sequence[str], None] = '0aab559cea97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "oauth_attempts",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.add_column(
        "oauth_attempts",
        sa.Column(
            "purpose",
            sa.String(length=50),
            nullable=False,
            server_default="login",
        ),
    )

    op.add_column(
        "oauth_attempts",
        sa.Column(
            "requested_scopes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )

    op.create_foreign_key(
        "fk_oauth_attempt_user",
        "oauth_attempts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.alter_column(
        "oauth_attempts",
        "purpose",
        server_default=None,
    )

    op.alter_column(
        "oauth_attempts",
        "requested_scopes",
        server_default=None,
    )


def downgrade():
    op.drop_constraint(
        "fk_oauth_attempt_user",
        "oauth_attempts",
        type_="foreignkey",
    )

    op.drop_column(
        "oauth_attempts",
        "requested_scopes",
    )

    op.drop_column(
        "oauth_attempts",
        "purpose",
    )

    op.drop_column(
        "oauth_attempts",
        "user_id",
    )
