"""add execution event sequence

Revision ID: 834c89f3896f
Revises: 480c027ddb70
Create Date: 2026-08-15 18:57:10.177572
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "834c89f3896f"
down_revision: Union[
    str,
    Sequence[str],
    None,
] = "480c027ddb70"
branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None
depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


SEQUENCE_NAME = "execution_event_sequence"


def upgrade() -> None:
    bind = op.get_bind()

    # PostgreSQL supplies all future event sequence numbers.
    op.execute(
        f"CREATE SEQUENCE {SEQUENCE_NAME}"
    )

    op.add_column(
        "execution_events",
        sa.Column(
            "sequence_number",
            sa.BigInteger(),
            nullable=True,
            server_default=sa.text(
                f"nextval('{SEQUENCE_NAME}')"
            ),
        ),
    )

    # Historical events did not have an explicit ordering
    # number. Give them a stable deterministic order based on
    # their existing timestamp and UUID.
    bind.execute(
        sa.text(
            f"""
            WITH ordered_events AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        ORDER BY created_at ASC, id ASC
                    ) AS sequence_number
                FROM execution_events
            )
            UPDATE execution_events AS event
            SET sequence_number =
                ordered.sequence_number
            FROM ordered_events AS ordered
            WHERE event.id = ordered.id
            """
        )
    )

    max_sequence = bind.execute(
        sa.text(
            """
            SELECT COALESCE(
                MAX(sequence_number),
                0
            )
            FROM execution_events
            """
        )
    ).scalar_one()

    # Ensure the next database-generated value follows all
    # historical events.
    if max_sequence > 0:
        bind.execute(
            sa.text(
                f"""
                SELECT setval(
                    '{SEQUENCE_NAME}',
                    :max_sequence,
                    true
                )
                """
            ),
            {
                "max_sequence":
                    max_sequence,
            },
        )

    op.alter_column(
        "execution_events",
        "sequence_number",
        existing_type=sa.BigInteger(),
        nullable=False,
        existing_server_default=sa.text(
            f"nextval('{SEQUENCE_NAME}')"
        ),
    )

    op.create_index(
        "ix_execution_events_sequence_number",
        "execution_events",
        ["sequence_number"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_execution_events_sequence_number",
        table_name="execution_events",
    )

    op.drop_column(
        "execution_events",
        "sequence_number",
    )

    op.execute(
        f"DROP SEQUENCE {SEQUENCE_NAME}"
    )