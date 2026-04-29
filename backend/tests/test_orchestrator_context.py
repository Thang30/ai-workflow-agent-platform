import os
import unittest
from types import SimpleNamespace

os.environ.setdefault(
    "DATABASE_URL", "postgresql://localhost:5432/ai_workflow_agent_platform_test"
)
os.environ.setdefault("HF_TOKEN", "test-token")
os.environ.setdefault("MODEL", "test-model")

from app.core.orchestrator import WorkflowOrchestrator
from app.models.trace import WorkflowAttempt


class StubExecutor:
    def __init__(self):
        self.last_query = None

    def execute(self, query: str) -> dict:
        self.last_query = query
        return {"output": "step result", "tools": []}


class StubRepository:
    def __init__(self):
        self.progress_updates: list[dict] = []
        self.complete_payload: dict | None = None

    def create_attempt(
        self,
        run_id: str,
        *,
        attempt_number: int,
        retry_trigger: str | None = None,
        improvement_hint: str | None = None,
        assignment=None,
    ) -> WorkflowAttempt:
        return WorkflowAttempt(
            id="attempt-1",
            run_id=run_id,
            attempt_number=attempt_number,
            status="running",
            created_at="2026-04-29T00:00:00Z",
        )

    def update_attempt_progress(
        self,
        attempt_id: str,
        *,
        plan=None,
        traces=None,
        had_tool_failure=None,
    ):
        self.progress_updates.append(
            {
                "attempt_id": attempt_id,
                "plan": list(plan or []),
                "traces": list(traces or []),
                "had_tool_failure": had_tool_failure,
            }
        )

    def complete_attempt(self, attempt_id: str, **kwargs) -> WorkflowAttempt:
        self.complete_payload = {"attempt_id": attempt_id, **kwargs}
        return WorkflowAttempt(
            id=attempt_id,
            run_id="run-1",
            attempt_number=1,
            status="completed",
            created_at="2026-04-29T00:00:00Z",
            had_tool_failure=kwargs["had_tool_failure"],
            final_answer=kwargs["final_answer"],
            evaluation_score=kwargs["evaluation_score"],
            evaluation_reason=kwargs["evaluation_reason"],
            plan=kwargs["plan"],
            traces=kwargs["traces"],
        )

    def fail_attempt(self, attempt_id: str, **kwargs) -> WorkflowAttempt:
        raise AssertionError(f"Unexpected fail_attempt call: {attempt_id}, {kwargs}")


class OrchestratorContextTests(unittest.TestCase):
    def test_execute_step_includes_original_user_request(self):
        orchestrator = WorkflowOrchestrator()
        executor = StubExecutor()
        agents = SimpleNamespace(executor=executor)

        result_entry, trace, next_context = orchestrator._execute_step(
            agents,
            "Calculate compound interest on $10,000 at 7.5% APR for 5 years.",
            {"step": 1, "description": "Calculate the final amount."},
            "Step 0: principal=10000, apr=0.075, years=5",
        )

        self.assertIn("Original user request:", executor.last_query)
        self.assertIn("$10,000", executor.last_query)
        self.assertIn("Context so far:", executor.last_query)
        self.assertIn("Current step:", executor.last_query)
        self.assertEqual(result_entry["result"], "step result")
        self.assertEqual(trace["output"], "step result")
        self.assertIn("Step 1: step result", next_context)

    def test_run_attempt_tracks_tool_failures_and_persists_progress(self):
        repository = StubRepository()
        orchestrator = WorkflowOrchestrator(repository=repository)

        def plan_run(query: str, improvement_hint: str | None = None):
            return [{"step": 1, "description": "Use the tool"}]

        def execute(query: str):
            return {
                "output": "step result",
                "tools": [{"success": False, "error_message": "Tool failed"}],
            }

        def review_run(
            query: str,
            plan: list,
            formatted_results: str,
            improvement_hint: str | None = None,
        ):
            return "final answer"

        def evaluate_run(query: str, final_answer: str):
            return {"score": 7, "reasoning": "Recovered despite tool failure."}

        agents = SimpleNamespace(
            planner=SimpleNamespace(run=plan_run),
            executor=SimpleNamespace(execute=execute),
            reviewer=SimpleNamespace(run=review_run),
            evaluator=SimpleNamespace(run=evaluate_run),
        )

        attempt = orchestrator._run_attempt("run-1", "Question", 1, agents)

        self.assertEqual(len(repository.progress_updates), 2)
        self.assertTrue(repository.progress_updates[-1]["had_tool_failure"])
        self.assertIsNotNone(repository.complete_payload)
        self.assertTrue(repository.complete_payload["had_tool_failure"])
        self.assertEqual(attempt.final_answer, "final answer")
        self.assertEqual(len(attempt.traces), 1)
