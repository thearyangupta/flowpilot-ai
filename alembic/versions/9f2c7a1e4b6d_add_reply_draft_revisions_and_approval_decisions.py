"""add reply draft revisions and approval decisions

Revision ID: 9f2c7a1e4b6d
Revises: 38adef0c16ca
"""

import hashlib
import json
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "9f2c7a1e4b6d"
down_revision = "38adef0c16ca"
branch_labels = None
depends_on = None


def _hash_content(content: dict) -> str:
    canonical = json.dumps(
        content,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()


def upgrade() -> None:
    op.create_table(
        "reply_draft_revisions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "reply_draft_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "revision_number",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "content",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "content_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "created_by_actor",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reply_draft_id"],
            ["reply_drafts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reply_draft_id",
            "revision_number",
            name="uq_reply_draft_revisions_draft_revision",
        ),
    )

    op.create_index(
        "ix_reply_draft_revisions_reply_draft_id",
        "reply_draft_revisions",
        ["reply_draft_id"],
        unique=False,
    )

    op.create_index(
        "ix_reply_draft_revisions_user_id",
        "reply_draft_revisions",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_reply_draft_revisions_user_draft",
        "reply_draft_revisions",
        ["user_id", "reply_draft_id"],
        unique=False,
    )

    op.create_table(
        "approval_decisions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "revision_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "action",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.String(length=1000),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["reply_draft_revisions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_approval_decisions_revision_id",
        "approval_decisions",
        ["revision_id"],
        unique=False,
    )

    op.create_index(
        "ix_approval_decisions_user_id",
        "approval_decisions",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_approval_decisions_user_revision",
        "approval_decisions",
        ["user_id", "revision_id"],
        unique=False,
    )

    op.add_column(
        "reply_drafts",
        sa.Column(
            "current_revision_number",
            sa.Integer(),
            nullable=True,
        ),
    )

    connection = op.get_bind()

    revisions = sa.table(
        "reply_draft_revisions",
        sa.column(
            "id",
            postgresql.UUID(as_uuid=True),
        ),
        sa.column(
            "reply_draft_id",
            postgresql.UUID(as_uuid=True),
        ),
        sa.column(
            "user_id",
            postgresql.UUID(as_uuid=True),
        ),
        sa.column(
            "revision_number",
            sa.Integer(),
        ),
        sa.column(
            "content",
            postgresql.JSONB(),
        ),
        sa.column(
            "content_hash",
            sa.String(),
        ),
        sa.column(
            "created_by_actor",
            sa.String(),
        ),
        sa.column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
        ),
        sa.column(
            "created_at",
            sa.DateTime(timezone=True),
        ),
    )

    existing_drafts = connection.execute(
        sa.text(
            """
            SELECT
                id,
                user_id,
                draft_message,
                created_at
            FROM reply_drafts
            """
        )
    ).mappings().all()

    if existing_drafts:
        rows = []

        for draft in existing_drafts:
            content = draft["draft_message"] or {}

            rows.append(
                {
                    "id": uuid4(),
                    "reply_draft_id": draft["id"],
                    "user_id": draft["user_id"],
                    "revision_number": 1,
                    "content": content,
                    "content_hash": _hash_content(content),
                    "created_by_actor": "migration_snapshot",
                    "created_by_user_id": None,
                    "created_at": draft["created_at"],
                }
            )

        connection.execute(
            revisions.insert(),
            rows,
        )

    connection.execute(
        sa.text(
            """
            UPDATE reply_drafts
            SET current_revision_number = 1
            WHERE current_revision_number IS NULL
            """
        )
    )

    op.alter_column(
        "reply_drafts",
        "current_revision_number",
        existing_type=sa.Integer(),
        nullable=False,
        server_default="1",
    )


def downgrade() -> None:
    op.drop_column(
        "reply_drafts",
        "current_revision_number",
    )

    op.drop_index(
        "ix_approval_decisions_user_revision",
        table_name="approval_decisions",
    )
    op.drop_index(
        "ix_approval_decisions_user_id",
        table_name="approval_decisions",
    )
    op.drop_index(
        "ix_approval_decisions_revision_id",
        table_name="approval_decisions",
    )
    op.drop_table(
        "approval_decisions",
    )

    op.drop_index(
        "ix_reply_draft_revisions_user_draft",
        table_name="reply_draft_revisions",
    )
    op.drop_index(
        "ix_reply_draft_revisions_user_id",
        table_name="reply_draft_revisions",
    )
    op.drop_index(
        "ix_reply_draft_revisions_reply_draft_id",
        table_name="reply_draft_revisions",
    )
    op.drop_table(
        "reply_draft_revisions",
    )
