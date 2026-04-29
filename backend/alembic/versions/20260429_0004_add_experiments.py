"""add experiments

Revision ID: 20260429_0004
Revises: 20260429_0003
Create Date: 2026-04-29 02:00:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260429_0004"
down_revision = "20260429_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
        sa.Column(
            "assignment_strategy",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'random'"),
        ),
        sa.Column("prompt_key", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        op.f("ix_experiments_created_at"), "experiments", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_experiments_prompt_key"), "experiments", ["prompt_key"], unique=False
    )
    op.create_index(
        op.f("ix_experiments_status"), "experiments", ["status"], unique=False
    )
    op.create_index(op.f("ix_experiments_type"), "experiments", ["type"], unique=False)

    op.create_table(
        "experiment_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=8), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["experiments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "experiment_id",
            "name",
            name="uq_experiment_variants_experiment_id_name",
        ),
    )
    op.create_index(
        op.f("ix_experiment_variants_experiment_id"),
        "experiment_variants",
        ["experiment_id"],
        unique=False,
    )

    op.add_column(
        "workflow_runs",
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("experiment_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("experiment_type", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("variant_name", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column(
            "variant_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_workflow_runs_experiment_id",
        "workflow_runs",
        "experiments",
        ["experiment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_workflow_runs_variant_id",
        "workflow_runs",
        "experiment_variants",
        ["variant_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_workflow_runs_experiment_id"),
        "workflow_runs",
        ["experiment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workflow_runs_experiment_type"),
        "workflow_runs",
        ["experiment_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workflow_runs_variant_id"),
        "workflow_runs",
        ["variant_id"],
        unique=False,
    )

    op.add_column(
        "workflow_attempts",
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "workflow_attempts",
        sa.Column("experiment_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "workflow_attempts",
        sa.Column("experiment_type", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "workflow_attempts",
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "workflow_attempts",
        sa.Column("variant_name", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "workflow_attempts",
        sa.Column(
            "variant_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_workflow_attempts_experiment_id",
        "workflow_attempts",
        "experiments",
        ["experiment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_workflow_attempts_variant_id",
        "workflow_attempts",
        "experiment_variants",
        ["variant_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_workflow_attempts_experiment_id"),
        "workflow_attempts",
        ["experiment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workflow_attempts_experiment_type"),
        "workflow_attempts",
        ["experiment_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workflow_attempts_variant_id"),
        "workflow_attempts",
        ["variant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_workflow_attempts_variant_id"), table_name="workflow_attempts"
    )
    op.drop_index(
        op.f("ix_workflow_attempts_experiment_type"), table_name="workflow_attempts"
    )
    op.drop_index(
        op.f("ix_workflow_attempts_experiment_id"), table_name="workflow_attempts"
    )
    op.drop_constraint(
        "fk_workflow_attempts_variant_id", "workflow_attempts", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_workflow_attempts_experiment_id", "workflow_attempts", type_="foreignkey"
    )
    op.drop_column("workflow_attempts", "variant_config")
    op.drop_column("workflow_attempts", "variant_name")
    op.drop_column("workflow_attempts", "variant_id")
    op.drop_column("workflow_attempts", "experiment_type")
    op.drop_column("workflow_attempts", "experiment_name")
    op.drop_column("workflow_attempts", "experiment_id")

    op.drop_index(op.f("ix_workflow_runs_variant_id"), table_name="workflow_runs")
    op.drop_index(op.f("ix_workflow_runs_experiment_type"), table_name="workflow_runs")
    op.drop_index(op.f("ix_workflow_runs_experiment_id"), table_name="workflow_runs")
    op.drop_constraint(
        "fk_workflow_runs_variant_id", "workflow_runs", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_workflow_runs_experiment_id", "workflow_runs", type_="foreignkey"
    )
    op.drop_column("workflow_runs", "variant_config")
    op.drop_column("workflow_runs", "variant_name")
    op.drop_column("workflow_runs", "variant_id")
    op.drop_column("workflow_runs", "experiment_type")
    op.drop_column("workflow_runs", "experiment_name")
    op.drop_column("workflow_runs", "experiment_id")

    op.drop_index(
        op.f("ix_experiment_variants_experiment_id"), table_name="experiment_variants"
    )
    op.drop_table("experiment_variants")

    op.drop_index(op.f("ix_experiments_type"), table_name="experiments")
    op.drop_index(op.f("ix_experiments_status"), table_name="experiments")
    op.drop_index(op.f("ix_experiments_prompt_key"), table_name="experiments")
    op.drop_index(op.f("ix_experiments_created_at"), table_name="experiments")
    op.drop_table("experiments")
