from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ExperimentAssignment:
    experiment_id: str | None
    experiment_name: str
    experiment_type: str
    variant_id: str | None
    variant_name: str
    variant_config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StepTrace:
    step: int
    description: str
    input: str
    output: str
    tools: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WorkflowRun:
    id: str
    query: str
    status: str
    created_at: str
    experiment: ExperimentAssignment | None = None
    attempt_count: int = 0
    selected_attempt_number: int | None = None
    final_answer: str | None = None
    evaluation_score: int | None = None
    evaluation_reason: str | None = None
    confidence_level: str | None = None
    reasoning_summary: str | None = None
    duration_ms: int | None = None
    completed_at: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WorkflowAttempt:
    id: str
    run_id: str
    attempt_number: int
    status: str
    created_at: str
    experiment: ExperimentAssignment | None = None
    retry_trigger: str | None = None
    improvement_hint: str | None = None
    had_tool_failure: bool = False
    final_answer: str | None = None
    evaluation_score: int | None = None
    evaluation_reason: str | None = None
    confidence_level: str | None = None
    reasoning_summary: str | None = None
    duration_ms: int | None = None
    completed_at: str | None = None
    error_message: str | None = None
    plan: list[dict[str, Any]] = field(default_factory=list)
    traces: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WorkflowRunSummary:
    id: str
    query: str
    status: str
    created_at: str
    experiment: ExperimentAssignment | None = None
    attempt_count: int = 0
    selected_attempt_number: int | None = None
    final_answer: str | None = None
    evaluation_score: int | None = None
    duration_ms: int | None = None
    completed_at: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WorkflowRunEnvelope:
    input: str
    plan: list[dict[str, Any]] = field(default_factory=list)
    traces: list[dict[str, Any]] = field(default_factory=list)
    final: str | None = None
    workflow_run: WorkflowRun | None = None
    attempts: list[WorkflowAttempt] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": self.input,
            "plan": self.plan,
            "traces": self.traces,
            "final": self.final,
            "workflow_run": self.workflow_run.to_dict() if self.workflow_run else None,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


@dataclass(slots=True)
class WorkflowRunList:
    items: list[WorkflowRunSummary]
    page: int
    page_size: int
    total: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "page": self.page,
            "page_size": self.page_size,
            "total": self.total,
        }


@dataclass(slots=True)
class WorkflowRunStats:
    total_runs: int
    average_score: float | None
    last_run_at: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalyticsSummary:
    total_runs: int
    average_score: float | None
    failure_rate: float | None
    average_duration_ms: float | None
    p95_duration_ms: int | None
    retry_rate: float | None = None
    successful_retry_rate: float | None = None
    average_attempts_per_run: float | None = None
    average_score_improvement: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalyticsTimeSeriesPoint:
    date: str
    total_runs: int
    average_score: float | None
    failure_rate: float | None
    average_duration_ms: float | None
    retry_rate: float | None = None
    average_attempts_per_run: float | None = None
    average_score_improvement: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalyticsTimeSeries:
    items: list[AnalyticsTimeSeriesPoint]

    def to_dict(self) -> dict[str, Any]:
        return {"items": [item.to_dict() for item in self.items]}


@dataclass(slots=True)
class AnalyticsDistributionBucket:
    key: str
    label: str
    count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalyticsDistribution:
    items: list[AnalyticsDistributionBucket]

    def to_dict(self) -> dict[str, Any]:
        return {"items": [item.to_dict() for item in self.items]}


@dataclass(slots=True)
class AnalyticsToolUsage:
    name: str
    call_count: int
    run_count: int
    share: float
    average_duration_ms: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalyticsToolUsageList:
    items: list[AnalyticsToolUsage]

    def to_dict(self) -> dict[str, Any]:
        return {"items": [item.to_dict() for item in self.items]}


@dataclass(slots=True)
class AnalyticsExperimentVariantSummary:
    variant_name: str
    variant_config: dict[str, Any] = field(default_factory=dict)
    run_count: int = 0
    average_score: float | None = None
    average_duration_ms: float | None = None
    failure_rate: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalyticsExperimentSummary:
    experiment_name: str
    experiment_type: str
    variants: list[AnalyticsExperimentVariantSummary]

    def to_dict(self) -> dict[str, Any]:
        return {
            "variants": [item.to_dict() for item in self.variants],
            "experiment_name": self.experiment_name,
            "experiment_type": self.experiment_type,
        }
