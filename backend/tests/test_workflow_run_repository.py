import os
import unittest

os.environ.setdefault(
    "DATABASE_URL", "postgresql://localhost:5432/ai_workflow_agent_platform_test"
)
os.environ.setdefault("HF_TOKEN", "test-token")
os.environ.setdefault("MODEL", "test-model")

from app.repositories.workflow_runs import (  # noqa: E402
    RUN_STATUS_COMPLETED,
    RUN_STATUS_FAILED,
    _build_reasoning_summary,
    _derive_confidence_level,
)


class WorkflowRunRepositoryDerivationTests(unittest.TestCase):
    def test_derive_confidence_level_uses_score_thresholds(self):
        self.assertEqual(_derive_confidence_level(8), "high")
        self.assertEqual(_derive_confidence_level(10), "high")
        self.assertEqual(_derive_confidence_level(6), "medium")
        self.assertEqual(_derive_confidence_level(7), "medium")
        self.assertEqual(_derive_confidence_level(5), "low")
        self.assertEqual(_derive_confidence_level(0), "low")
        self.assertIsNone(_derive_confidence_level(None))

    def test_build_reasoning_summary_combines_plan_tools_and_evaluation(self):
        summary = _build_reasoning_summary(
            plan=[
                {"step": 1, "description": "Fetch the latest date"},
                {"step": 2, "description": "Draft the answer"},
            ],
            traces=[
                {
                    "step": 1,
                    "description": "Fetch the latest date",
                    "tools": [{"name": "Current Date/Time"}],
                },
                {
                    "step": 2,
                    "description": "Draft the answer",
                    "tools": [],
                },
            ],
            evaluation_reason="The answer is grounded in the captured tool output.",
            status=RUN_STATUS_COMPLETED,
        )

        self.assertIsNotNone(summary)
        self.assertIn("2-step plan", summary)
        self.assertIn("1 tool call", summary)
        self.assertIn("Current Date/Time", summary)
        self.assertIn(
            "The answer is grounded in the captured tool output.",
            summary,
        )

    def test_build_reasoning_summary_handles_failed_unscored_runs(self):
        summary = _build_reasoning_summary(
            plan=[
                {"step": 1, "description": "Search the docs"},
                {"step": 2, "description": "Draft the answer"},
                {"step": 3, "description": "Review the answer"},
            ],
            traces=[
                {
                    "step": 1,
                    "description": "Search the docs",
                    "tools": [],
                }
            ],
            evaluation_reason=None,
            status=RUN_STATUS_FAILED,
        )

        self.assertIsNotNone(summary)
        self.assertIn("planned 3 steps and completed 1 before it stopped", summary)
        self.assertIn("without recorded tool calls", summary)
        self.assertIn("did not produce a scored final answer", summary)

    def test_build_reasoning_summary_returns_none_for_empty_payloads(self):
        self.assertIsNone(
            _build_reasoning_summary(
                plan=[],
                traces=[],
                evaluation_reason=None,
                status=RUN_STATUS_COMPLETED,
            )
        )


if __name__ == "__main__":
    unittest.main()