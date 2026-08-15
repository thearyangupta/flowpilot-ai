"""add project ownership

Revision ID: 480c027ddb70
Revises: 9f2c7a1e4b6d
Create Date: 2026-08-15 18:31:12.366820
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "480c027ddb70"
down_revision: Union[str, Sequence[str], None] = "9f2c7a1e4b6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Add the ownership column as nullable first so existing
    # development projects can be migrated safely.
    op.add_column(
        "projects",
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    project_count = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM projects
            """
        )
    ).scalar_one()

    if project_count > 0:
        user_ids = list(
            bind.execute(
                sa.text(
                    """
                    SELECT id
                    FROM users
                    ORDER BY created_at ASC
                    """
                )
            ).scalars()
        )

        if len(user_ids) != 1:
            raise RuntimeError(
                "Cannot safely backfill project ownership: "
                "existing projects require exactly one "
                "existing user."
            )

        bind.execute(
            sa.text(
                """
                UPDATE projects
                SET user_id = :user_id
                WHERE user_id IS NULL
                """
            ),
            {
                "user_id": user_ids[0],
            },
        )

    # After historical rows are assigned, ownership becomes a
    # required invariant for every project.
    op.alter_column(
        "projects",
        "user_id",
        existing_type=sa.UUID(),
        nullable=False,
    )

    op.create_foreign_key(
        "fk_projects_user_id_users",
        "projects",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_projects_user_id",
        "projects",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_projects_user_id",
        table_name="projects",
    )

    op.drop_constraint(
        "fk_projects_user_id_users",
        "projects",
        type_="foreignkey",
    )

    op.drop_column(
        "projects",
        "user_id",
    )
