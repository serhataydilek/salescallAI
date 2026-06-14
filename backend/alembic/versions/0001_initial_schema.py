"""Initial schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-14 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


call_status = sa.Enum("uploaded", "transcribed", "analyzed", "failed", name="callstatus")


def upgrade() -> None:
    op.create_table(
        "calls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("status", call_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_calls_id"), "calls", ["id"], unique=False)

    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("call_id", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("opening_score", sa.Integer(), nullable=False),
        sa.Column("discovery_score", sa.Integer(), nullable=False),
        sa.Column("objection_handling_score", sa.Integer(), nullable=False),
        sa.Column("closing_score", sa.Integer(), nullable=False),
        sa.Column("follow_up_score", sa.Integer(), nullable=False),
        sa.Column("talk_ratio_feedback", sa.Text(), nullable=False),
        sa.Column("top_3_mistakes", sa.JSON(), nullable=False),
        sa.Column("missed_questions", sa.JSON(), nullable=False),
        sa.Column("suggested_improvements", sa.JSON(), nullable=False),
        sa.Column("better_example_responses", sa.JSON(), nullable=False),
        sa.Column("short_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("call_id"),
    )
    op.create_index(op.f("ix_analyses_id"), "analyses", ["id"], unique=False)

    op.create_table(
        "transcripts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("call_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("call_id"),
    )
    op.create_index(op.f("ix_transcripts_id"), "transcripts", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transcripts_id"), table_name="transcripts")
    op.drop_table("transcripts")
    op.drop_index(op.f("ix_analyses_id"), table_name="analyses")
    op.drop_table("analyses")
    op.drop_index(op.f("ix_calls_id"), table_name="calls")
    op.drop_table("calls")
    call_status.drop(op.get_bind(), checkfirst=True)
