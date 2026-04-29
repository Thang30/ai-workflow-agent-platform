import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.executor_agent import ExecutorAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.core.config import settings
from app.models.trace import (
    StepTrace,
    WorkflowAttempt,
    WorkflowRun,
    WorkflowRunEnvelope,
)
from app.repositories.workflow_runs import RUN_STATUS_COMPLETED, WorkflowRunRepository


def save_trace(data):
    filename = f"trace_{datetime.now().timestamp()}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


@dataclass(slots=True)
class RetryDecision:
    should_retry: bool
    trigger: str | None = None
    improvement_hint: str | None = None


class WorkflowOrchestrator:
    def __init__(self, repository: WorkflowRunRepository | None = None):
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.reviewer = ReviewerAgent()
        self.evaluator = EvaluationAgent()
        self.repository = repository or WorkflowRunRepository()

    def _stream_event(self, event: str, data):
        return {"event": event, "data": json.dumps(data, ensure_ascii=False)}

    def _execute_step(self, step: dict, context: str):
        step_desc = step["description"]
        enriched_input = f"""
            Context so far:
            {context}

            Current step:
            {step_desc}
            """

        execution = self.executor.execute(enriched_input)
        result = execution["output"]
        tools = execution["tools"]

        trace = StepTrace(
            step=step["step"],
            description=step_desc,
            input=enriched_input,
            output=result,
            tools=tools,
        ).to_dict()

        next_context = f"{context}\nStep {step['step']}: {result}\n"
        result_entry = {
            "step": step["step"],
            "description": step_desc,
            "result": result,
            "tools": tools,
        }

        return result_entry, trace, next_context

    def _review_workflow(
        self,
        query: str,
        plan: list,
        results: list,
        improvement_hint: str | None = None,
    ) -> str:
        formatted_results = "\n".join(
            [f"Step {result['step']}: {result['result']}" for result in results]
        )

        return self.reviewer.run(
            query,
            plan,
            formatted_results,
            improvement_hint=improvement_hint,
        )

    def _evaluate_workflow(self, query: str, final_answer: str) -> dict:
        return self.evaluator.run(query, final_answer)

    def _build_payload(
        self,
        query: str,
        workflow_run: WorkflowRun,
        selected_attempt: WorkflowAttempt | None = None,
        attempts: list[WorkflowAttempt] | None = None,
    ) -> WorkflowRunEnvelope:
        return WorkflowRunEnvelope(
            input=query,
            plan=selected_attempt.plan if selected_attempt else [],
            traces=selected_attempt.traces if selected_attempt else [],
            final=workflow_run.final_answer,
            workflow_run=workflow_run,
            attempts=attempts or [],
        )

    def _save_workflow_run(
        self,
        workflow_payload: WorkflowRunEnvelope,
    ):
        save_trace(workflow_payload.to_dict())

    def _elapsed_duration_ms(self, started_at: float) -> int:
        return max(0, round((perf_counter() - started_at) * 1000))

    def _step_has_tool_failure(self, tools: list[dict]) -> bool:
        return any(
            isinstance(tool, dict)
            and (tool.get("success") is False or bool(tool.get("error_message")))
            for tool in tools
        )

    def _build_retry_decision(self, attempt: WorkflowAttempt) -> RetryDecision:
        trigger_parts: list[str] = []
        guidance_parts: list[str] = []

        if attempt.status != RUN_STATUS_COMPLETED:
            trigger_parts.append("attempt_failure")
            guidance_parts.append("The previous attempt failed before completing.")

        if attempt.had_tool_failure:
            trigger_parts.append("tool_failure")
            guidance_parts.append(
                "A required tool failed or returned unavailable data. Recover gracefully and be explicit about missing information."
            )

        if (
            attempt.evaluation_score is not None
            and attempt.evaluation_score < settings.self_improvement_low_score_threshold
        ):
            trigger_parts.append("low_score")
            guidance_parts.append(
                f"The evaluation score was {attempt.evaluation_score}/10, below the threshold of {settings.self_improvement_low_score_threshold}."
            )

        if not trigger_parts:
            return RetryDecision(should_retry=False)

        if attempt.evaluation_reason:
            guidance_parts.append(f"Evaluator feedback: {attempt.evaluation_reason}")

        if attempt.error_message:
            guidance_parts.append(f"Failure details: {attempt.error_message}")

        guidance_parts.append(
            "Improve the next attempt by being more concrete, complete, and transparent about any remaining uncertainty."
        )

        return RetryDecision(
            should_retry=True,
            trigger=", ".join(trigger_parts),
            improvement_hint="\n".join(guidance_parts),
        )

    def _select_best_attempt(self, attempts: list[WorkflowAttempt]) -> WorkflowAttempt:
        return max(
            attempts,
            key=lambda attempt: (
                (
                    attempt.evaluation_score
                    if attempt.evaluation_score is not None
                    else -1
                ),
                1 if attempt.status == RUN_STATUS_COMPLETED else 0,
                -attempt.attempt_number,
            ),
        )

    def _finalize_run(
        self,
        run_id: str,
        query: str,
        attempts: list[WorkflowAttempt],
        started_at: float,
    ) -> WorkflowRunEnvelope:
        selected_attempt = self._select_best_attempt(attempts)
        workflow_run = self.repository.finalize_run(
            run_id,
            selected_attempt=selected_attempt,
            duration_ms=self._elapsed_duration_ms(started_at),
            completed_at=datetime.now(timezone.utc),
        )
        payload = self._build_payload(
            query,
            workflow_run,
            selected_attempt=selected_attempt,
            attempts=attempts,
        )
        self._save_workflow_run(payload)
        return payload

    def _finalize_failure(
        self,
        run_id: str,
        query: str,
        error: Exception,
        started_at: float,
    ) -> WorkflowRunEnvelope:
        workflow_run = self.repository.fail_run(
            run_id,
            plan=[],
            traces=[],
            error_message=str(error),
            duration_ms=self._elapsed_duration_ms(started_at),
            completed_at=datetime.now(timezone.utc),
            final_answer=None,
        )
        payload = self._build_payload(query, workflow_run)
        self._save_workflow_run(payload)
        return payload

    def _run_attempt(
        self,
        run_id: str,
        query: str,
        attempt_number: int,
        retry_trigger: str | None = None,
        improvement_hint: str | None = None,
    ) -> WorkflowAttempt:
        attempt_record = self.repository.create_attempt(
            run_id,
            attempt_number=attempt_number,
            retry_trigger=retry_trigger,
            improvement_hint=improvement_hint,
        )
        attempt_started_at = perf_counter()

        plan = []
        results = []
        context = ""
        traces = []
        final_answer: str | None = None
        had_tool_failure = False

        try:
            plan = self.planner.run(query, improvement_hint=improvement_hint)
            self.repository.update_attempt_progress(
                attempt_record.id,
                plan=plan,
                traces=traces,
                had_tool_failure=had_tool_failure,
            )

            for step in plan:
                result_entry, trace, context = self._execute_step(step, context)
                traces.append(trace)
                results.append(result_entry)
                had_tool_failure = had_tool_failure or self._step_has_tool_failure(
                    result_entry["tools"]
                )
                self.repository.update_attempt_progress(
                    attempt_record.id,
                    plan=plan,
                    traces=traces,
                    had_tool_failure=had_tool_failure,
                )

            final_answer = self._review_workflow(
                query,
                plan,
                results,
                improvement_hint=improvement_hint,
            )
            evaluation = self._evaluate_workflow(query, final_answer)

            return self.repository.complete_attempt(
                attempt_record.id,
                plan=plan,
                traces=traces,
                final_answer=final_answer,
                evaluation_score=evaluation["score"],
                evaluation_reason=evaluation["reasoning"],
                duration_ms=self._elapsed_duration_ms(attempt_started_at),
                completed_at=datetime.now(timezone.utc),
                had_tool_failure=had_tool_failure,
            )
        except Exception as error:
            return self.repository.fail_attempt(
                attempt_record.id,
                plan=plan,
                traces=traces,
                error_message=str(error),
                duration_ms=self._elapsed_duration_ms(attempt_started_at),
                completed_at=datetime.now(timezone.utc),
                final_answer=final_answer,
                had_tool_failure=had_tool_failure,
            )

    def list_runs(self, page: int = 1, page_size: int = 20) -> dict:
        return self.repository.list_runs(page=page, page_size=page_size).to_dict()

    def get_run(self, run_id: str) -> dict | None:
        run = self.repository.get_run(run_id)
        return run.to_dict() if run else None

    def get_run_stats(self) -> dict:
        return self.repository.get_run_stats().to_dict()

    def get_analytics_summary(self, days: int = 7) -> dict:
        return self.repository.get_analytics_summary(days=days).to_dict()

    def get_analytics_timeseries(self, days: int = 7) -> dict:
        return self.repository.get_analytics_timeseries(days=days).to_dict()

    def get_analytics_distribution(self, days: int = 7) -> dict:
        return self.repository.get_analytics_distribution(days=days).to_dict()

    def get_analytics_tools(self, days: int = 7) -> dict:
        return self.repository.get_analytics_tools(days=days).to_dict()

    def run(self, query: str):
        run_record = self.repository.create_run(query)
        started_at = perf_counter()
        attempts: list[WorkflowAttempt] = []
        retry_trigger: str | None = None
        improvement_hint: str | None = None

        try:
            for attempt_number in range(1, settings.self_improvement_max_retries + 2):
                attempt = self._run_attempt(
                    run_record.id,
                    query,
                    attempt_number,
                    retry_trigger=retry_trigger,
                    improvement_hint=improvement_hint,
                )
                attempts.append(attempt)

                retry_decision = self._build_retry_decision(attempt)
                can_retry = attempt_number <= settings.self_improvement_max_retries
                if not retry_decision.should_retry or not can_retry:
                    break

                retry_trigger = retry_decision.trigger
                improvement_hint = retry_decision.improvement_hint

            payload = self._finalize_run(
                run_record.id,
                query,
                attempts,
                started_at,
            )
            return payload.to_dict()
        except Exception as error:
            payload = self._finalize_failure(
                run_record.id,
                query,
                error,
                started_at,
            )
            return payload.to_dict()

    async def stream_events(self, query: str):
        run_record = self.repository.create_run(query)
        started_at = perf_counter()
        attempts: list[WorkflowAttempt] = []
        retry_trigger: str | None = None
        improvement_hint: str | None = None

        try:
            for attempt_number in range(1, settings.self_improvement_max_retries + 2):
                attempt_record = self.repository.create_attempt(
                    run_record.id,
                    attempt_number=attempt_number,
                    retry_trigger=retry_trigger,
                    improvement_hint=improvement_hint,
                )

                yield self._stream_event(
                    "attempt_start",
                    {
                        "attempt_number": attempt_number,
                        "retry_trigger": retry_trigger,
                        "improvement_hint": improvement_hint,
                    },
                )
                yield self._stream_event(
                    "status",
                    f"🧠 Planning attempt {attempt_number}...",
                )

                attempt_started_at = perf_counter()
                plan = []
                results = []
                traces = []
                context = ""
                final_answer: str | None = None
                had_tool_failure = False

                try:
                    plan = self.planner.run(query, improvement_hint=improvement_hint)
                    self.repository.update_attempt_progress(
                        attempt_record.id,
                        plan=plan,
                        traces=traces,
                        had_tool_failure=had_tool_failure,
                    )

                    yield self._stream_event(
                        "plan",
                        {"attempt_number": attempt_number, "plan": plan},
                    )
                    yield self._stream_event(
                        "status",
                        f"⚙️ Executing attempt {attempt_number}...",
                    )

                    for step in plan:
                        yield self._stream_event(
                            "step_start",
                            {
                                "attempt_number": attempt_number,
                                "step": step["step"],
                                "description": step["description"],
                            },
                        )

                        result_entry, trace, context = self._execute_step(step, context)
                        traces.append(trace)
                        results.append(result_entry)
                        had_tool_failure = (
                            had_tool_failure
                            or self._step_has_tool_failure(result_entry["tools"])
                        )
                        self.repository.update_attempt_progress(
                            attempt_record.id,
                            plan=plan,
                            traces=traces,
                            had_tool_failure=had_tool_failure,
                        )

                        yield self._stream_event(
                            "step_done",
                            {
                                "attempt_number": attempt_number,
                                "step": step["step"],
                                "output": result_entry["result"],
                                "tools": result_entry["tools"],
                            },
                        )

                        await asyncio.sleep(0.1)

                    yield self._stream_event(
                        "status",
                        f"🔍 Reviewing attempt {attempt_number}...",
                    )
                    final_answer = self._review_workflow(
                        query,
                        plan,
                        results,
                        improvement_hint=improvement_hint,
                    )

                    yield self._stream_event(
                        "status",
                        f"📏 Evaluating attempt {attempt_number}...",
                    )
                    evaluation = self._evaluate_workflow(query, final_answer)
                    attempt = self.repository.complete_attempt(
                        attempt_record.id,
                        plan=plan,
                        traces=traces,
                        final_answer=final_answer,
                        evaluation_score=evaluation["score"],
                        evaluation_reason=evaluation["reasoning"],
                        duration_ms=self._elapsed_duration_ms(attempt_started_at),
                        completed_at=datetime.now(timezone.utc),
                        had_tool_failure=had_tool_failure,
                    )
                except Exception as error:
                    attempt = self.repository.fail_attempt(
                        attempt_record.id,
                        plan=plan,
                        traces=traces,
                        error_message=str(error),
                        duration_ms=self._elapsed_duration_ms(attempt_started_at),
                        completed_at=datetime.now(timezone.utc),
                        final_answer=final_answer,
                        had_tool_failure=had_tool_failure,
                    )

                attempts.append(attempt)
                yield self._stream_event("attempt_complete", attempt.to_dict())

                retry_decision = self._build_retry_decision(attempt)
                can_retry = attempt_number <= settings.self_improvement_max_retries
                if not retry_decision.should_retry or not can_retry:
                    break

                retry_trigger = retry_decision.trigger
                improvement_hint = retry_decision.improvement_hint
                yield self._stream_event(
                    "status",
                    f"🔁 Retrying with attempt {attempt_number + 1}...",
                )

            payload = self._finalize_run(
                run_record.id,
                query,
                attempts,
                started_at,
            )
            yield self._stream_event(
                "status",
                (
                    "✅ Completed"
                    if payload.workflow_run
                    and payload.workflow_run.status == RUN_STATUS_COMPLETED
                    else "❌ Failed"
                ),
            )
            yield self._stream_event("final", payload.to_dict())
        except Exception as error:
            payload = self._finalize_failure(
                run_record.id,
                query,
                error,
                started_at,
            )
            yield self._stream_event("status", "❌ Failed")
            yield self._stream_event("final", payload.to_dict())
