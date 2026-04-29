import os
import unittest
from types import SimpleNamespace

os.environ.setdefault(
    "DATABASE_URL", "postgresql://localhost:5432/ai_workflow_agent_platform_test"
)
os.environ.setdefault("HF_TOKEN", "test-token")
os.environ.setdefault("MODEL", "test-model")

from app.core.orchestrator import WorkflowOrchestrator


class StubExecutor:
    def __init__(self):
        self.last_query = None

    def execute(self, query: str) -> dict:
        self.last_query = query
        return {"output": "step result", "tools": []}


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
