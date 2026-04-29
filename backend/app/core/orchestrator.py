import asyncio
import json
from datetime import datetime, timezone
from time import perf_counter

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.executor_agent import ExecutorAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.models.trace import StepTrace, WorkflowRun, WorkflowRunEnvelope
from app.repositories.workflow_runs import WorkflowRunRepository


def save_trace(data):
    filename = f"trace_{datetime.now().timestamp()}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


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
    ) -> str:
        formatted_results = "\n".join(
            [f"Step {result['step']}: {result['result']}" for result in results]
        )

        return self.reviewer.run(query, plan, formatted_results)

    def _evaluate_workflow(self, query: str, final_answer: str) -> dict:
        return self.evaluator.run(query, final_answer)

    def _build_payload(
        self,
        query: str,
        plan: list,
        traces: list,
        workflow_run: WorkflowRun,
    ) -> WorkflowRunEnvelope:
        return WorkflowRunEnvelope(
            input=query,
            plan=plan,
            traces=traces,
            final=workflow_run.final_answer,
            workflow_run=workflow_run,
        )

    def _save_workflow_run(
        self,
        workflow_payload: WorkflowRunEnvelope,
    ):
        save_trace(workflow_payload.to_dict())

    def _elapsed_duration_ms(self, started_at: float) -> int:
        return max(0, round((perf_counter() - started_at) * 1000))

    def _finalize_success(
        self,
        run_id: str,
        query: str,
        plan: list,
        traces: list,
        final_answer: str,
        started_at: float,
    ) -> WorkflowRunEnvelope:
        evaluation = self._evaluate_workflow(query, final_answer)
        workflow_run = self.repository.complete_run(
            run_id,
            plan=plan,
            traces=traces,
            final_answer=final_answer,
            evaluation_score=evaluation["score"],
            evaluation_reason=evaluation["reasoning"],
            duration_ms=self._elapsed_duration_ms(started_at),
            completed_at=datetime.now(timezone.utc),
        )
        payload = self._build_payload(query, plan, traces, workflow_run)
        self._save_workflow_run(payload)
        return payload

    def _finalize_failure(
        self,
        run_id: str,
        query: str,
        plan: list,
        traces: list,
        error: Exception,
        started_at: float,
        final_answer: str | None = None,
    ) -> WorkflowRunEnvelope:
        workflow_run = self.repository.fail_run(
            run_id,
            plan=plan,
            traces=traces,
            error_message=str(error),
            duration_ms=self._elapsed_duration_ms(started_at),
            completed_at=datetime.now(timezone.utc),
            final_answer=final_answer,
        )
        payload = self._build_payload(query, plan, traces, workflow_run)
        self._save_workflow_run(payload)
        return payload

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
        """
        Full workflow:
        1. Generate plan
        2. Execute each step
        3. Collect results
        """

        run_record = self.repository.create_run(query)
        started_at = perf_counter()

        plan = []
        results = []
        context = ""
        traces = []
        final_answer: str | None = None

        try:
            plan = self.planner.run(query)
            self.repository.update_run_progress(run_record.id, plan=plan)

            for step in plan:
                result_entry, trace, context = self._execute_step(step, context)
                traces.append(trace)
                results.append(result_entry)
                self.repository.update_run_progress(
                    run_record.id,
                    plan=plan,
                    traces=traces,
                )

            final_answer = self._review_workflow(query, plan, results)
            payload = self._finalize_success(
                run_record.id,
                query,
                plan,
                traces,
                final_answer,
                started_at,
            )
            return payload.to_dict()
        except Exception as error:
            payload = self._finalize_failure(
                run_record.id,
                query,
                plan,
                traces,
                error,
                started_at,
                final_answer=final_answer,
            )
            return payload.to_dict()

    async def stream_events(self, query: str):
        run_record = self.repository.create_run(query)
        started_at = perf_counter()

        yield self._stream_event("status", "🧠 Planning...")

        plan = []
        results = []
        traces = []
        context = ""
        final_answer: str | None = None

        try:
            plan = self.planner.run(query)
            self.repository.update_run_progress(run_record.id, plan=plan)

            yield self._stream_event("plan", plan)
            yield self._stream_event("status", "⚙️ Executing...")

            for step in plan:
                yield self._stream_event(
                    "step_start",
                    {"step": step["step"], "description": step["description"]},
                )

                result_entry, trace, context = self._execute_step(step, context)
                traces.append(trace)
                results.append(result_entry)
                self.repository.update_run_progress(
                    run_record.id,
                    plan=plan,
                    traces=traces,
                )

                yield self._stream_event(
                    "step_done",
                    {
                        "step": step["step"],
                        "output": result_entry["result"],
                        "tools": result_entry["tools"],
                    },
                )

                await asyncio.sleep(0.1)

            yield self._stream_event("status", "🔍 Reviewing...")

            final_answer = self._review_workflow(query, plan, results)

            yield self._stream_event("status", "📏 Evaluating...")

            payload = self._finalize_success(
                run_record.id,
                query,
                plan,
                traces,
                final_answer,
                started_at,
            )
            yield self._stream_event("final", payload.workflow_run.to_dict())
        except Exception as error:
            payload = self._finalize_failure(
                run_record.id,
                query,
                plan,
                traces,
                error,
                started_at,
                final_answer=final_answer,
            )
            yield self._stream_event("status", "❌ Failed")
            yield self._stream_event("final", payload.workflow_run.to_dict())
