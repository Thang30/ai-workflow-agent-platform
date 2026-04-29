from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.core.db import SessionLocal
from app.models.trace import (
    WorkflowRun,
    WorkflowRunEnvelope,
    WorkflowRunList,
    WorkflowRunStats,
    WorkflowRunSummary,
)
from app.models.workflow_run import WorkflowRunModel

RUN_STATUS_RUNNING = "running"
RUN_STATUS_COMPLETED = "completed"
RUN_STATUS_FAILED = "failed"


def _serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.isoformat()

    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_run_id(run_id: str) -> UUID:
    return UUID(run_id)


def _build_run(record: WorkflowRunModel) -> WorkflowRun:
    return WorkflowRun(
        id=str(record.id),
        query=record.query,
        status=record.status,
        created_at=_serialize_datetime(record.created_at) or "",
        final_answer=record.final_answer,
        evaluation_score=record.evaluation_score,
        evaluation_reason=record.evaluation_reason,
        duration_ms=record.duration_ms,
        completed_at=_serialize_datetime(record.completed_at),
        error_message=record.error_message,
    )


def _build_summary(record: WorkflowRunModel) -> WorkflowRunSummary:
    return WorkflowRunSummary(
        id=str(record.id),
        query=record.query,
        status=record.status,
        created_at=_serialize_datetime(record.created_at) or "",
        final_answer=record.final_answer,
        evaluation_score=record.evaluation_score,
        duration_ms=record.duration_ms,
        completed_at=_serialize_datetime(record.completed_at),
        error_message=record.error_message,
    )


def _build_envelope(record: WorkflowRunModel) -> WorkflowRunEnvelope:
    workflow_run = _build_run(record)
    return WorkflowRunEnvelope(
        input=record.query,
        plan=record.plan or [],
        traces=record.traces or [],
        final=workflow_run.final_answer,
        workflow_run=workflow_run,
    )


class WorkflowRunRepository:
    def __init__(self, session_factory: sessionmaker = SessionLocal):
        self.session_factory = session_factory

    def create_run(self, query: str) -> WorkflowRun:
        with self.session_factory() as session:
            record = WorkflowRunModel(query=query, status=RUN_STATUS_RUNNING)
            session.add(record)
            session.commit()
            session.refresh(record)
            return _build_run(record)

    def update_run_progress(
        self,
        run_id: str,
        *,
        plan: list[dict] | None = None,
        traces: list[dict] | None = None,
    ) -> WorkflowRun:
        with self.session_factory() as session:
            record = session.get(WorkflowRunModel, _parse_run_id(run_id))
            if record is None:
                raise ValueError(f"Unknown workflow run: {run_id}")

            if plan is not None:
                record.plan = plan

            if traces is not None:
                record.traces = traces

            session.commit()
            session.refresh(record)
            return _build_run(record)

    def complete_run(
        self,
        run_id: str,
        *,
        plan: list[dict],
        traces: list[dict],
        final_answer: str,
        evaluation_score: int,
        evaluation_reason: str,
        duration_ms: int,
        completed_at: datetime,
    ) -> WorkflowRun:
        with self.session_factory() as session:
            record = session.get(WorkflowRunModel, _parse_run_id(run_id))
            if record is None:
                raise ValueError(f"Unknown workflow run: {run_id}")

            record.status = RUN_STATUS_COMPLETED
            record.plan = plan
            record.traces = traces
            record.final_answer = final_answer
            record.evaluation_score = evaluation_score
            record.evaluation_reason = evaluation_reason
            record.duration_ms = duration_ms
            record.completed_at = completed_at

            session.commit()
            session.refresh(record)
            return _build_run(record)

    def fail_run(
        self,
        run_id: str,
        *,
        plan: list[dict],
        traces: list[dict],
        error_message: str,
        duration_ms: int,
        completed_at: datetime,
        final_answer: str | None = None,
    ) -> WorkflowRun:
        with self.session_factory() as session:
            record = session.get(WorkflowRunModel, _parse_run_id(run_id))
            if record is None:
                raise ValueError(f"Unknown workflow run: {run_id}")

            record.status = RUN_STATUS_FAILED
            record.plan = plan
            record.traces = traces
            record.final_answer = final_answer
            record.error_message = error_message
            record.duration_ms = duration_ms
            record.completed_at = completed_at

            session.commit()
            session.refresh(record)
            return _build_run(record)

    def list_runs(self, page: int = 1, page_size: int = 20) -> WorkflowRunList:
        with self.session_factory() as session:
            total = (
                session.scalar(select(func.count()).select_from(WorkflowRunModel)) or 0
            )
            statement = (
                select(WorkflowRunModel)
                .order_by(WorkflowRunModel.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            records = session.scalars(statement).all()

            return WorkflowRunList(
                items=[_build_summary(record) for record in records],
                page=page,
                page_size=page_size,
                total=total,
            )

    def get_run(self, run_id: str) -> WorkflowRunEnvelope | None:
        with self.session_factory() as session:
            record = session.get(WorkflowRunModel, _parse_run_id(run_id))
            if record is None:
                return None

            return _build_envelope(record)

    def get_run_stats(self) -> WorkflowRunStats:
        with self.session_factory() as session:
            total_runs, average_score, last_run_at = session.execute(
                select(
                    func.count(WorkflowRunModel.id),
                    func.avg(WorkflowRunModel.evaluation_score),
                    func.max(WorkflowRunModel.created_at),
                )
            ).one()

            return WorkflowRunStats(
                total_runs=int(total_runs or 0),
                average_score=(
                    round(float(average_score), 2)
                    if average_score is not None
                    else None
                ),
                last_run_at=_serialize_datetime(last_run_at),
            )
