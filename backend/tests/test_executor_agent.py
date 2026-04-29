import os
import unittest

os.environ.setdefault("DATABASE_URL", "postgresql://localhost:5432/ai_workflow_agent_platform_test")
os.environ.setdefault("HF_TOKEN", "test-token")
os.environ.setdefault("MODEL", "test-model")

from app.agents.executor_agent import ExecutorAgent
from app.tools.common import build_tool_response
from app.tools.registry import ToolDefinition


class StubLLM:
    def __init__(self, responses: list[str]):
        self.responses = list(responses)
        self.prompts: list[str] = []

    def chat(self, prompt: str, model: str | None = None) -> str:
        self.prompts.append(prompt)
        if not self.responses:
            raise AssertionError("No stub LLM responses remaining")

        return self.responses.pop(0)


class ExecutorAgentTests(unittest.TestCase):
    def test_execute_uses_structured_calculator_tool_selection(self):
        tool_calls: list[tuple[str, bool]] = []

        def fake_calculator(tool_input: str, structured: bool = False):
            tool_calls.append((tool_input, structured))
            return build_tool_response(
                tool_input=tool_input,
                raw_output={"results": [{"display": "12.76"}], "final_value": 12.76},
                started_at="2026-04-29T00:00:00Z",
                finished_at="2026-04-29T00:00:00Z",
                elapsed_seconds=0.01,
                preview="12.76",
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
                '{"action":"use_tool","tool_name":"calculator","tool_input":"10000 * (1 + 0.075 / 12) ** (12 * 5)","reason":"requires precise calculation"}',
                "The calculated result is 12.76.",
            ]
        )

        result = agent.execute("Current step:\nCalculate compound interest.")

        self.assertEqual(result["output"], "The calculated result is 12.76.")
        self.assertEqual(
            tool_calls,
            [("10000 * (1 + 0.075 / 12) ** (12 * 5)", True)],
        )
        self.assertEqual(len(result["tools"]), 1)
        self.assertEqual(result["tools"][0]["name"], "Calculator")
        self.assertEqual(
            result["tools"][0]["input"],
            "10000 * (1 + 0.075 / 12) ** (12 * 5)",
        )
        self.assertEqual(
            result["tools"][0]["reason"],
            "requires precise calculation",
        )

    def test_execute_routes_to_current_datetime_tool(self):
        tool_calls: list[tuple[str, bool]] = []

        def fake_current_datetime(tool_input: str, structured: bool = False):
            tool_calls.append((tool_input, structured))
            return build_tool_response(
                tool_input=tool_input,
                raw_output={
                    "local_iso": "2026-04-29T10:15:00+00:00",
                    "utc_iso": "2026-04-29T10:15:00Z",
                    "weekday": "Wednesday",
                },
                started_at="2026-04-29T00:00:00Z",
                finished_at="2026-04-29T00:00:00Z",
                elapsed_seconds=0.01,
                preview="Local: 2026-04-29T10:15:00+00:00\nUTC: 2026-04-29T10:15:00Z\nWeekday: Wednesday",
                success=True,
            )

        agent = ExecutorAgent(
            tools={
                "current_datetime": ToolDefinition(
                    key="current_datetime",
                    display_name="Current Date/Time",
                    description="Return current local and UTC date and time.",
                    handler=fake_current_datetime,
                )
            }
        )
        agent.llm = StubLLM(
            [
                '{"action":"use_tool","tool_name":"current_datetime","tool_input":"Need today\'s weekday and time","reason":"requires the current date and time"}',
                "Today is Wednesday and the current UTC time is 10:15.",
            ]
        )

        result = agent.execute("Current step:\nWhat day is it today and what time is it?")

        self.assertEqual(
            tool_calls,
            [("Need today's weekday and time", True)],
        )
        self.assertEqual(result["tools"][0]["name"], "Current Date/Time")
        self.assertEqual(result["tools"][0]["input"], "Need today's weekday and time")
        self.assertEqual(
            result["output"],
            "Today is Wednesday and the current UTC time is 10:15.",
        )

    def test_execute_falls_back_to_direct_response_on_invalid_json(self):
        agent = ExecutorAgent(tools={})
        agent.llm = StubLLM(
            [
                "This is not valid JSON.",
                "No tool is needed for this step.",
            ]
        )

        result = agent.execute("Current step:\nSummarize the prior results.")

        self.assertEqual(result["output"], "No tool is needed for this step.")
        self.assertEqual(result["tools"], [])
        self.assertEqual(len(agent.llm.prompts), 2)

    def test_execute_records_unknown_tool_failure(self):
        agent = ExecutorAgent(tools={})
        agent.llm = StubLLM(
            [
                '{"action":"use_tool","tool_name":"python","tool_input":"print(2+2)","reason":"needs math"}',
                "I could not use the requested tool, so I am answering with that limitation.",
            ]
        )

        result = agent.execute("Current step:\nCompute 2 + 2.")

        self.assertEqual(len(result["tools"]), 1)
        self.assertFalse(result["tools"][0]["success"])
        self.assertIn("Unknown tool requested", result["tools"][0]["error_message"])
        self.assertEqual(
            result["output"],
            "I could not use the requested tool, so I am answering with that limitation.",
        )