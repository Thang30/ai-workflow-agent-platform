import os
import unittest

os.environ.setdefault(
    "DATABASE_URL", "postgresql://localhost:5432/ai_workflow_agent_platform_test"
)
os.environ.setdefault("HF_TOKEN", "test-token")
os.environ.setdefault("MODEL", "test-model")

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.executor_agent import ExecutorAgent
from app.agents.planner_agent import PlannerAgent
from app.tools.common import build_tool_response
from app.tools.registry import ToolDefinition


class StubLLM:
    def __init__(self, responses: list[str]):
        self.responses = list(responses)

    def chat(self, prompt: str, model: str | None = None) -> str:
        if not self.responses:
            raise AssertionError("No stub LLM responses remaining")

        return self.responses.pop(0)


class AgentParsingTests(unittest.TestCase):
    def test_planner_parses_fenced_json_with_trailing_commas(self):
        planner = PlannerAgent()
        planner.llm = StubLLM(
            ['```json\n[{"step": 1, "description": "Search docs",}]\n```']
        )

        result = planner.run("Find the latest docs")

        self.assertEqual(
            result,
            [{"step": 1, "description": "Search docs"}],
        )

    def test_executor_parses_fenced_tool_decision_with_trailing_commas(self):
        tool_calls: list[tuple[str, bool]] = []

        def fake_calculator(tool_input: str, structured: bool = False):
            tool_calls.append((tool_input, structured))
            return build_tool_response(
                tool_input=tool_input,
                raw_output={"result": 4},
                started_at="2026-04-29T00:00:00Z",
                finished_at="2026-04-29T00:00:00Z",
                elapsed_seconds=0,
                preview="4",
                success=True,
            )

        agent = ExecutorAgent(
            tools={
                "calculator": ToolDefinition(
                    key="calculator",
                    display_name="Calculator",
                    description="Evaluate arithmetic expressions.",
                    handler=fake_calculator,
                )
            }
        )
        agent.llm = StubLLM(
            [
                '```json\n{"action": "use_tool", "tool_name": "calculator", "tool_input": "2 + 2", "reason": "needs math",}\n```',
                "The answer is 4.",
            ]
        )

        result = agent.execute("Current step:\nCompute 2 + 2.")

        self.assertEqual(tool_calls, [("2 + 2", True)])
        self.assertEqual(result["output"], "The answer is 4.")
        self.assertEqual(result["tools"][0]["name"], "Calculator")

    def test_evaluator_parses_fenced_json_object(self):
        evaluator = EvaluationAgent()
        evaluator.llm = StubLLM(
            ['```json\n{"score": 8.6, "reasoning": "Solid evidence."}\n```']
        )

        result = evaluator.run("Question", "Answer")

        self.assertEqual(result["score"], 9)
        self.assertEqual(result["reasoning"], "Solid evidence.")


if __name__ == "__main__":
    unittest.main()
