"""add workflow attempts

Revision ID: 20260429_0003
Revises: 20260429_0002
Create Date: 2026-04-29 01:00:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260429_0003"
down_revision = "20260429_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflow_runs",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("selected_attempt_number", sa.Integer(), nullable=True),
    )

    op.execute("""
        UPDATE workflow_runs
        SET attempt_count = CASE WHEN status = 'running' THEN 0 ELSE 1 END,
            selected_attempt_number = CASE WHEN status = 'running' THEN NULL ELSE 1 END
        """)

    op.create_table(
        "workflow_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("retry_trigger", sa.Text(), nullable=True),
        sa.Column("improvement_hint", sa.Text(), nullable=True),
        sa.Column(
            "had_tool_failure",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "plan",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "traces",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("final_answer", sa.Text(), nullable=True),
        sa.Column("evaluation_score", sa.Integer(), nullable=True),
        sa.Column("evaluation_reason", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["workflow_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id",
            "attempt_number",
            name="uq_workflow_attempts_run_id_attempt_number",
        ),
    )

    op.create_index(
        op.f("ix_workflow_attempts_run_id"),
        "workflow_attempts",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workflow_attempts_status"),
        "workflow_attempts",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workflow_attempts_evaluation_score"),
        "workflow_attempts",
        ["evaluation_score"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workflow_attempts_completed_at"),
        "workflow_attempts",
        ["completed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_workflow_attempts_completed_at"),
        table_name="workflow_attempts",
    )
    op.drop_index(
        op.f("ix_workflow_attempts_evaluation_score"),
        table_name="workflow_attempts",
    )
    op.drop_index(op.f("ix_workflow_attempts_status"), table_name="workflow_attempts")
    op.drop_index(op.f("ix_workflow_attempts_run_id"), table_name="workflow_attempts")
    op.drop_table("workflow_attempts")

    op.drop_column("workflow_runs", "selected_attempt_number")
    op.drop_column("workflow_runs", "attempt_count")
