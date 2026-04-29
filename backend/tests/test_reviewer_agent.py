import os
import unittest

os.environ.setdefault(
    "DATABASE_URL", "postgresql://localhost:5432/ai_workflow_agent_platform_test"
)
os.environ.setdefault("HF_TOKEN", "test-token")
os.environ.setdefault("MODEL", "test-model")

from app.agents.reviewer_agent import ReviewerAgent


class StubLLM:
    def __init__(self, response: str):
        self.response = response
        self.prompts: list[str] = []

    def chat(self, prompt: str, model: str | None = None) -> str:
        self.prompts.append(prompt)
        return self.response


class ReviewerAgentTests(unittest.TestCase):
    def test_run_passes_string_prompt_to_llm(self):
        reviewer = ReviewerAgent()
        reviewer.llm = StubLLM("Final synthesized answer")

        result = reviewer.run(
            "What is 2+2?",
            [{"step": 1, "description": "Compute 2+2"}],
            "Step 1: 4",
        )

        self.assertEqual(result, "Final synthesized answer")
        self.assertEqual(len(reviewer.llm.prompts), 1)
        self.assertIsInstance(reviewer.llm.prompts[0], str)
        self.assertIn("What is 2+2?", reviewer.llm.prompts[0])
        self.assertIn("Step 1: 4", reviewer.llm.prompts[0])