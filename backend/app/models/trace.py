from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


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
    final_answer: str | None = None
    evaluation_score: int | None = None
    evaluation_reason: str | None = None
    duration_ms: int | None = None
    completed_at: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WorkflowRunSummary:
    id: str
    query: str
    status: str
    created_at: str
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": self.input,
            "plan": self.plan,
            "traces": self.traces,
            "final": self.final,
            "workflow_run": self.workflow_run.to_dict() if self.workflow_run else None,
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
