"""add workflow run analytics indexes

Revision ID: 20260429_0002
Revises: 20260429_0001
Create Date: 2026-04-29 00:30:00.000000

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260429_0002"
down_revision = "20260429_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        op.f("ix_workflow_runs_completed_at"),
        "workflow_runs",
        ["completed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workflow_runs_duration_ms"),
        "workflow_runs",
        ["duration_ms"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workflow_runs_evaluation_score"),
        "workflow_runs",
        ["evaluation_score"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_workflow_runs_evaluation_score"), table_name="workflow_runs")
    op.drop_index(op.f("ix_workflow_runs_duration_ms"), table_name="workflow_runs")
    op.drop_index(op.f("ix_workflow_runs_completed_at"), table_name="workflow_runs")
