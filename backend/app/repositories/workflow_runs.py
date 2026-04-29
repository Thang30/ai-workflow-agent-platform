from __future__ import annotations

from datetime import datetime, timedelta, timezone
from collections import defaultdict
from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.db import SessionLocal
from app.models.trace import (
    AnalyticsDistribution,
    AnalyticsDistributionBucket,
    AnalyticsSummary,
    AnalyticsTimeSeries,
    AnalyticsTimeSeriesPoint,
    WorkflowAttempt,
    AnalyticsToolUsage,
    AnalyticsToolUsageList,
    WorkflowRun,
    WorkflowRunEnvelope,
    WorkflowRunList,
    WorkflowRunStats,
    WorkflowRunSummary,
)
from app.models.workflow_run import WorkflowAttemptModel, WorkflowRunModel

RUN_STATUS_RUNNING = "running"
RUN_STATUS_COMPLETED = "completed"
RUN_STATUS_FAILED = "failed"

SCORE_DISTRIBUTION_BUCKETS = (
    ("0_5", "0-5"),
    ("6_7", "6-7"),
    ("8_10", "8-10"),
)


def _serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.isoformat()

    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_run_id(run_id: str) -> UUID:
    return UUID(run_id)


def _parse_attempt_id(attempt_id: str) -> UUID:
    return UUID(attempt_id)


def _round_float(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None

    return round(float(value), digits)


def _window_start(days: int) -> datetime:
    utc_today = datetime.now(timezone.utc).date()
    start_date = utc_today - timedelta(days=max(days - 1, 0))
    return datetime(
        start_date.year,
        start_date.month,
        start_date.day,
        tzinfo=timezone.utc,
    )


def _analytics_timestamp():
    return func.coalesce(WorkflowRunModel.completed_at, WorkflowRunModel.created_at)


def _failure_condition():
    return or_(
        WorkflowRunModel.status == RUN_STATUS_FAILED,
        WorkflowRunModel.evaluation_score
        < settings.self_improvement_low_score_threshold,
    )


def _analytics_conditions(days: int) -> list:
    return [
        WorkflowRunModel.status != RUN_STATUS_RUNNING,
        _analytics_timestamp() >= _window_start(days),
    ]


def _build_run(record: WorkflowRunModel) -> WorkflowRun:
    return WorkflowRun(
        id=str(record.id),
        query=record.query,
        status=record.status,
        created_at=_serialize_datetime(record.created_at) or "",
        attempt_count=record.attempt_count,
        selected_attempt_number=record.selected_attempt_number,
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
        attempt_count=record.attempt_count,
        selected_attempt_number=record.selected_attempt_number,
        final_answer=record.final_answer,
        evaluation_score=record.evaluation_score,
        duration_ms=record.duration_ms,
        completed_at=_serialize_datetime(record.completed_at),
        error_message=record.error_message,
    )


def _build_attempt(record: WorkflowAttemptModel) -> WorkflowAttempt:
    return WorkflowAttempt(
        id=str(record.id),
        run_id=str(record.run_id),
        attempt_number=record.attempt_number,
        status=record.status,
        created_at=_serialize_datetime(record.created_at) or "",
        retry_trigger=record.retry_trigger,
        improvement_hint=record.improvement_hint,
        had_tool_failure=record.had_tool_failure,
        final_answer=record.final_answer,
        evaluation_score=record.evaluation_score,
        evaluation_reason=record.evaluation_reason,
        duration_ms=record.duration_ms,
        completed_at=_serialize_datetime(record.completed_at),
        error_message=record.error_message,
        plan=record.plan or [],
        traces=record.traces or [],
    )


def _build_envelope(
    record: WorkflowRunModel,
    attempts: list[WorkflowAttempt] | None = None,
) -> WorkflowRunEnvelope:
    workflow_run = _build_run(record)
    return WorkflowRunEnvelope(
        input=record.query,
        plan=record.plan or [],
        traces=record.traces or [],
        final=workflow_run.final_answer,
        workflow_run=workflow_run,
        attempts=attempts or [],
    )


class WorkflowRunRepository:
    def __init__(self, session_factory: sessionmaker = SessionLocal):
        self.session_factory = session_factory

    def _get_attempt_records(
        self,
        session,
        run_id: UUID,
    ) -> list[WorkflowAttemptModel]:
        statement = (
            select(WorkflowAttemptModel)
            .where(WorkflowAttemptModel.run_id == run_id)
            .order_by(WorkflowAttemptModel.attempt_number)
        )
        return session.scalars(statement).all()

    def _get_retry_metrics(self, session, days: int) -> dict:
        timestamp_column = _analytics_timestamp().label("analytics_at")
        run_rows = session.execute(
            select(
                WorkflowRunModel.id,
                WorkflowRunModel.attempt_count,
                WorkflowRunModel.selected_attempt_number,
                timestamp_column,
            ).where(*_analytics_conditions(days))
        ).all()

        run_ids = [row.id for row in run_rows]
        attempts_by_run: dict[UUID, list] = defaultdict(list)
        if run_ids:
            attempt_rows = session.execute(
                select(
                    WorkflowAttemptModel.run_id,
                    WorkflowAttemptModel.attempt_number,
                    WorkflowAttemptModel.status,
                    WorkflowAttemptModel.evaluation_score,
                )
                .where(WorkflowAttemptModel.run_id.in_(run_ids))
                .order_by(
                    WorkflowAttemptModel.run_id,
                    WorkflowAttemptModel.attempt_number,
                )
            ).all()

            for attempt_row in attempt_rows:
                attempts_by_run[attempt_row.run_id].append(attempt_row)

        summary_retry_runs = 0
        summary_successful_retry_runs = 0
        summary_attempt_total = 0
        summary_score_deltas: list[float] = []
        timeseries_metrics: dict[str, dict] = {}

        for row in run_rows:
            date_key = row.analytics_at.date().isoformat()
            metrics = timeseries_metrics.setdefault(
                date_key,
                {
                    "total_runs": 0,
                    "retry_runs": 0,
                    "successful_retry_runs": 0,
                    "attempt_total": 0,
                    "score_deltas": [],
                },
            )
            metrics["total_runs"] += 1

            attempts = attempts_by_run.get(row.id, [])
            attempt_count = max(row.attempt_count, len(attempts), 1)
            metrics["attempt_total"] += attempt_count
            summary_attempt_total += attempt_count

            if attempt_count <= 1:
                continue

            metrics["retry_runs"] += 1
            summary_retry_runs += 1

            first_attempt = next(
                (attempt for attempt in attempts if attempt.attempt_number == 1),
                attempts[0] if attempts else None,
            )
            selected_attempt = next(
                (
                    attempt
                    for attempt in attempts
                    if attempt.attempt_number == row.selected_attempt_number
                ),
                attempts[-1] if attempts else None,
            )

            if not first_attempt or not selected_attempt:
                continue

            retry_succeeded = (
                row.selected_attempt_number is not None
                and row.selected_attempt_number > 1
                and selected_attempt.status == RUN_STATUS_COMPLETED
                and (
                    first_attempt.status != RUN_STATUS_COMPLETED
                    or (
                        first_attempt.evaluation_score is not None
                        and selected_attempt.evaluation_score is not None
                        and selected_attempt.evaluation_score
                        > first_attempt.evaluation_score
                    )
                )
            )
            if retry_succeeded:
                metrics["successful_retry_runs"] += 1
                summary_successful_retry_runs += 1

            if (
                first_attempt.evaluation_score is not None
                and selected_attempt.evaluation_score is not None
            ):
                delta = float(
                    selected_attempt.evaluation_score - first_attempt.evaluation_score
                )
                metrics["score_deltas"].append(delta)
                summary_score_deltas.append(delta)

        total_runs = len(run_rows)
        summary = {
            "retry_rate": (
                round(summary_retry_runs / total_runs, 4) if total_runs else None
            ),
            "successful_retry_rate": (
                round(
                    summary_successful_retry_runs / summary_retry_runs,
                    4,
                )
                if summary_retry_runs
                else None
            ),
            "average_attempts_per_run": (
                round(summary_attempt_total / total_runs, 2) if total_runs else None
            ),
            "average_score_improvement": _round_float(
                sum(summary_score_deltas) / len(summary_score_deltas)
                if summary_score_deltas
                else None
            ),
        }

        for date_key, metrics in timeseries_metrics.items():
            total_runs_for_day = metrics["total_runs"]
            retry_runs_for_day = metrics["retry_runs"]
            metrics["retry_rate"] = (
                round(
                    retry_runs_for_day / total_runs_for_day,
                    4,
                )
                if total_runs_for_day
                else None
            )
            metrics["average_attempts_per_run"] = (
                round(
                    metrics["attempt_total"] / total_runs_for_day,
                    2,
                )
                if total_runs_for_day
                else None
            )
            metrics["average_score_improvement"] = _round_float(
                sum(metrics["score_deltas"]) / len(metrics["score_deltas"])
                if metrics["score_deltas"]
                else None
            )

        return {
            "summary": summary,
            "timeseries": timeseries_metrics,
        }

    def create_run(self, query: str) -> WorkflowRun:
        with self.session_factory() as session:
            record = WorkflowRunModel(
                query=query,
                status=RUN_STATUS_RUNNING,
                attempt_count=0,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return _build_run(record)

    def create_attempt(
        self,
        run_id: str,
        *,
        attempt_number: int,
        retry_trigger: str | None = None,
        improvement_hint: str | None = None,
    ) -> WorkflowAttempt:
        with self.session_factory() as session:
            run_record = session.get(WorkflowRunModel, _parse_run_id(run_id))
            if run_record is None:
                raise ValueError(f"Unknown workflow run: {run_id}")

            record = WorkflowAttemptModel(
                run_id=run_record.id,
                attempt_number=attempt_number,
                status=RUN_STATUS_RUNNING,
                retry_trigger=retry_trigger,
                improvement_hint=improvement_hint,
            )
            session.add(record)
            run_record.attempt_count = max(run_record.attempt_count, attempt_number)
            run_record.status = RUN_STATUS_RUNNING
            session.commit()
            session.refresh(record)
            return _build_attempt(record)

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

    def update_attempt_progress(
        self,
        attempt_id: str,
        *,
        plan: list[dict] | None = None,
        traces: list[dict] | None = None,
        had_tool_failure: bool | None = None,
    ) -> WorkflowAttempt:
        with self.session_factory() as session:
            record = session.get(WorkflowAttemptModel, _parse_attempt_id(attempt_id))
            if record is None:
                raise ValueError(f"Unknown workflow attempt: {attempt_id}")

            if plan is not None:
                record.plan = plan

            if traces is not None:
                record.traces = traces

            if had_tool_failure is not None:
                record.had_tool_failure = had_tool_failure

            run_record = session.get(WorkflowRunModel, record.run_id)
            if run_record is not None:
                run_record.plan = record.plan
                run_record.traces = record.traces

            session.commit()
            session.refresh(record)
            return _build_attempt(record)

    def complete_attempt(
        self,
        attempt_id: str,
        *,
        plan: list[dict],
        traces: list[dict],
        final_answer: str,
        evaluation_score: int,
        evaluation_reason: str,
        duration_ms: int,
        completed_at: datetime,
        had_tool_failure: bool = False,
    ) -> WorkflowAttempt:
        with self.session_factory() as session:
            record = session.get(WorkflowAttemptModel, _parse_attempt_id(attempt_id))
            if record is None:
                raise ValueError(f"Unknown workflow attempt: {attempt_id}")

            record.status = RUN_STATUS_COMPLETED
            record.plan = plan
            record.traces = traces
            record.final_answer = final_answer
            record.evaluation_score = evaluation_score
            record.evaluation_reason = evaluation_reason
            record.duration_ms = duration_ms
            record.completed_at = completed_at
            record.had_tool_failure = had_tool_failure

            run_record = session.get(WorkflowRunModel, record.run_id)
            if run_record is not None:
                run_record.plan = plan
                run_record.traces = traces

            session.commit()
            session.refresh(record)
            return _build_attempt(record)

    def fail_attempt(
        self,
        attempt_id: str,
        *,
        plan: list[dict],
        traces: list[dict],
        error_message: str,
        duration_ms: int,
        completed_at: datetime,
        final_answer: str | None = None,
        had_tool_failure: bool = False,
    ) -> WorkflowAttempt:
        with self.session_factory() as session:
            record = session.get(WorkflowAttemptModel, _parse_attempt_id(attempt_id))
            if record is None:
                raise ValueError(f"Unknown workflow attempt: {attempt_id}")

            record.status = RUN_STATUS_FAILED
            record.plan = plan
            record.traces = traces
            record.final_answer = final_answer
            record.error_message = error_message
            record.duration_ms = duration_ms
            record.completed_at = completed_at
            record.had_tool_failure = had_tool_failure

            run_record = session.get(WorkflowRunModel, record.run_id)
            if run_record is not None:
                run_record.plan = plan
                run_record.traces = traces

            session.commit()
            session.refresh(record)
            return _build_attempt(record)

    def finalize_run(
        self,
        run_id: str,
        *,
        selected_attempt: WorkflowAttempt,
        duration_ms: int,
        completed_at: datetime,
    ) -> WorkflowRun:
        with self.session_factory() as session:
            record = session.get(WorkflowRunModel, _parse_run_id(run_id))
            if record is None:
                raise ValueError(f"Unknown workflow run: {run_id}")

            record.status = selected_attempt.status
            record.attempt_count = max(
                record.attempt_count,
                selected_attempt.attempt_number,
            )
            record.selected_attempt_number = selected_attempt.attempt_number
            record.plan = selected_attempt.plan
            record.traces = selected_attempt.traces
            record.final_answer = selected_attempt.final_answer
            record.evaluation_score = selected_attempt.evaluation_score
            record.evaluation_reason = selected_attempt.evaluation_reason
            record.duration_ms = duration_ms
            record.error_message = selected_attempt.error_message
            record.completed_at = completed_at

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
            record.attempt_count = max(record.attempt_count, 1)
            record.selected_attempt_number = record.selected_attempt_number or 1
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
            record.attempt_count = max(record.attempt_count, 1)
            record.selected_attempt_number = record.selected_attempt_number or 1
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

            attempts = [
                _build_attempt(attempt_record)
                for attempt_record in self._get_attempt_records(session, record.id)
            ]
            return _build_envelope(record, attempts)

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

    def get_analytics_summary(self, days: int = 7) -> AnalyticsSummary:
        conditions = _analytics_conditions(days)
        failure_condition = _failure_condition()

        with self.session_factory() as session:
            total_runs, average_score, average_duration_ms, failure_count = (
                session.execute(
                    select(
                        func.count(WorkflowRunModel.id),
                        func.avg(WorkflowRunModel.evaluation_score),
                        func.avg(WorkflowRunModel.duration_ms),
                        func.sum(case((failure_condition, 1), else_=0)),
                    ).where(*conditions)
                ).one()
            )

            p95_duration_ms = session.scalar(
                select(
                    func.percentile_cont(0.95).within_group(
                        WorkflowRunModel.duration_ms
                    )
                ).where(*conditions, WorkflowRunModel.duration_ms.is_not(None))
            )
            retry_metrics = self._get_retry_metrics(session, days)

        total_runs = int(total_runs or 0)
        failure_count = int(failure_count or 0)

        return AnalyticsSummary(
            total_runs=total_runs,
            average_score=_round_float(average_score),
            failure_rate=(round(failure_count / total_runs, 4) if total_runs else None),
            average_duration_ms=_round_float(average_duration_ms),
            p95_duration_ms=(
                int(round(float(p95_duration_ms)))
                if p95_duration_ms is not None
                else None
            ),
            retry_rate=retry_metrics["summary"]["retry_rate"],
            successful_retry_rate=retry_metrics["summary"]["successful_retry_rate"],
            average_attempts_per_run=retry_metrics["summary"][
                "average_attempts_per_run"
            ],
            average_score_improvement=retry_metrics["summary"][
                "average_score_improvement"
            ],
        )

    def get_analytics_timeseries(self, days: int = 7) -> AnalyticsTimeSeries:
        conditions = _analytics_conditions(days)
        failure_condition = _failure_condition()
        timestamp_column = _analytics_timestamp()
        day_bucket = func.date_trunc("day", timestamp_column).label("day_bucket")

        with self.session_factory() as session:
            rows = session.execute(
                select(
                    day_bucket,
                    func.count(WorkflowRunModel.id),
                    func.avg(WorkflowRunModel.evaluation_score),
                    func.avg(WorkflowRunModel.duration_ms),
                    func.sum(case((failure_condition, 1), else_=0)),
                )
                .where(*conditions)
                .group_by(day_bucket)
                .order_by(day_bucket)
            ).all()
            retry_metrics = self._get_retry_metrics(session, days)

        indexed_rows: dict[str, AnalyticsTimeSeriesPoint] = {}
        for (
            day_value,
            total_runs,
            average_score,
            average_duration_ms,
            failure_count,
        ) in rows:
            date_key = day_value.date().isoformat()
            total_runs = int(total_runs or 0)
            failure_count = int(failure_count or 0)
            retry_day_metrics = retry_metrics["timeseries"].get(date_key, {})
            indexed_rows[date_key] = AnalyticsTimeSeriesPoint(
                date=date_key,
                total_runs=total_runs,
                average_score=_round_float(average_score),
                failure_rate=(
                    round(failure_count / total_runs, 4) if total_runs else None
                ),
                average_duration_ms=_round_float(average_duration_ms),
                retry_rate=retry_day_metrics.get("retry_rate"),
                average_attempts_per_run=retry_day_metrics.get(
                    "average_attempts_per_run"
                ),
                average_score_improvement=retry_day_metrics.get(
                    "average_score_improvement"
                ),
            )

        start_date = _window_start(days).date()
        end_date = datetime.now(timezone.utc).date()
        items: list[AnalyticsTimeSeriesPoint] = []
        current_date = start_date

        while current_date <= end_date:
            date_key = current_date.isoformat()
            items.append(
                indexed_rows.get(
                    date_key,
                    AnalyticsTimeSeriesPoint(
                        date=date_key,
                        total_runs=0,
                        average_score=None,
                        failure_rate=None,
                        average_duration_ms=None,
                        retry_rate=None,
                        average_attempts_per_run=None,
                        average_score_improvement=None,
                    ),
                )
            )
            current_date += timedelta(days=1)

        return AnalyticsTimeSeries(items=items)

    def get_analytics_distribution(self, days: int = 7) -> AnalyticsDistribution:
        conditions = [
            *_analytics_conditions(days),
            WorkflowRunModel.evaluation_score.is_not(None),
        ]
        bucket_key = case(
            (WorkflowRunModel.evaluation_score < 6, "0_5"),
            (WorkflowRunModel.evaluation_score < 8, "6_7"),
            else_="8_10",
        ).label("bucket_key")

        with self.session_factory() as session:
            rows = session.execute(
                select(bucket_key, func.count(WorkflowRunModel.id))
                .where(*conditions)
                .group_by(bucket_key)
            ).all()

        counts = {bucket: int(count or 0) for bucket, count in rows}

        return AnalyticsDistribution(
            items=[
                AnalyticsDistributionBucket(
                    key=key,
                    label=label,
                    count=counts.get(key, 0),
                )
                for key, label in SCORE_DISTRIBUTION_BUCKETS
            ]
        )

    def get_analytics_tools(self, days: int = 7) -> AnalyticsToolUsageList:
        conditions = _analytics_conditions(days)

        with self.session_factory() as session:
            rows = session.execute(
                select(WorkflowRunModel.id, WorkflowRunModel.traces).where(*conditions)
            ).all()

        tool_stats: dict[str, dict] = {}
        total_calls = 0

        for run_id, traces in rows:
            seen_in_run: set[str] = set()

            for trace in traces or []:
                tools = trace.get("tools") if isinstance(trace, dict) else None
                if not isinstance(tools, list):
                    continue

                for tool in tools:
                    if not isinstance(tool, dict):
                        continue

                    name = str(tool.get("name") or "Unknown tool")
                    stats = tool_stats.setdefault(
                        name,
                        {
                            "call_count": 0,
                            "run_ids": set(),
                            "duration_total": 0.0,
                            "duration_count": 0,
                        },
                    )

                    stats["call_count"] += 1
                    total_calls += 1

                    if name not in seen_in_run:
                        stats["run_ids"].add(str(run_id))
                        seen_in_run.add(name)

                    duration_ms = tool.get("duration_ms")
                    if isinstance(duration_ms, (int, float)):
                        stats["duration_total"] += float(duration_ms)
                        stats["duration_count"] += 1

        items = [
            AnalyticsToolUsage(
                name=name,
                call_count=stats["call_count"],
                run_count=len(stats["run_ids"]),
                share=(
                    round(stats["call_count"] / total_calls, 4) if total_calls else 0.0
                ),
                average_duration_ms=(
                    round(stats["duration_total"] / stats["duration_count"], 2)
                    if stats["duration_count"]
                    else None
                ),
            )
            for name, stats in sorted(
                tool_stats.items(),
                key=lambda item: (-item[1]["call_count"], item[0].lower()),
            )
        ]

        return AnalyticsToolUsageList(items=items)
