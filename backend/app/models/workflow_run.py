from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class WorkflowRunModel(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    selected_attempt_number: Mapped[int | None] = mapped_column(Integer)
    experiment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("experiments.id", ondelete="SET NULL"),
        index=True,
    )
    experiment_name: Mapped[str | None] = mapped_column(String(255))
    experiment_type: Mapped[str | None] = mapped_column(String(32), index=True)
    variant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("experiment_variants.id", ondelete="SET NULL"),
        index=True,
    )
    variant_name: Mapped[str | None] = mapped_column(String(8))
    variant_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    plan: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    traces: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    final_answer: Mapped[str | None] = mapped_column(Text)
    evaluation_score: Mapped[int | None] = mapped_column(Integer, index=True)
    evaluation_reason: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer, index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )


class WorkflowAttemptModel(Base):
    __tablename__ = "workflow_attempts"
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "attempt_number",
            name="uq_workflow_attempts_run_id_attempt_number",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    experiment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("experiments.id", ondelete="SET NULL"),
        index=True,
    )
    experiment_name: Mapped[str | None] = mapped_column(String(255))
    experiment_type: Mapped[str | None] = mapped_column(String(32), index=True)
    variant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("experiment_variants.id", ondelete="SET NULL"),
        index=True,
    )
    variant_name: Mapped[str | None] = mapped_column(String(8))
    variant_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    retry_trigger: Mapped[str | None] = mapped_column(Text)
    improvement_hint: Mapped[str | None] = mapped_column(Text)
    had_tool_failure: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    plan: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    traces: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    final_answer: Mapped[str | None] = mapped_column(Text)
    evaluation_score: Mapped[int | None] = mapped_column(Integer, index=True)
    evaluation_reason: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
