import os
import unittest

os.environ.setdefault(
    "DATABASE_URL", "postgresql://localhost:5432/ai_workflow_agent_platform_test"
)
os.environ.setdefault("HF_TOKEN", "test-token")
os.environ.setdefault("MODEL", "test-model")

from app.tools.calculator import calculate_expression
from app.tools.current_datetime import current_datetime


class SmallToolTests(unittest.TestCase):
    def test_calculator_evaluates_assignments_and_formula(self):
        result = calculate_expression(
            "principal = 10000\n"
            "rate = 0.075\n"
            "periods = 12\n"
            "year_1 = principal * (1 + rate / periods) ** (periods * 1)\n"
            "final_amount = principal * (1 + rate / periods) ** (periods * 5)",
            structured=True,
        )

        self.assertTrue(result["success"])
        self.assertIn("year_1 =", result["preview"])
        self.assertIn("final_amount =", result["preview"])
        self.assertAlmostEqual(result["raw_output"]["variables"]["principal"], 10000)

    def test_calculator_returns_failure_for_unknown_symbol(self):
        result = calculate_expression("annual_interest_rate / 12", structured=True)

        self.assertFalse(result["success"])
        self.assertIn("Unknown symbol", result["error_message"])
        self.assertIn("Calculator error", result["preview"])

    def test_calculator_supports_simple_range_loops_and_print(self):
        result = calculate_expression(
            "balance = 1000 * (1 + 0.41666667/100)^12.0\n"
            "for i in range(5):\n"
            "  balance *= (1 + 0.41666667/100)^12.0\n"
            "print(balance)",
            structured=True,
        )

        self.assertTrue(result["success"])
        self.assertIn("balance =", result["preview"])
        self.assertAlmostEqual(result["raw_output"]["variables"]["balance"], 1349.017747382953)

    def test_calculator_normalizes_labeled_lines(self):
        result = calculate_expression(
            "1000 * (1 + 0.0041666667)^4\n"
            "Year 1: 1000 * (1 + 0.0041666667)^1\n"
            "Year 2: 1000 * (1 + 0.0041666667)^2\n"
            "Year 3: 1000 * (1 + 0.0041666667)^3\n"
            "Year 4: 1000 * (1 + 0.0041666667)^4",
            structured=True,
        )

        self.assertTrue(result["success"])
        self.assertIn("year_1 =", result["preview"])
        self.assertIn("year_4 =", result["preview"])
        self.assertAlmostEqual(result["raw_output"]["variables"]["year_4"], 1016.7711231216003)

    def test_current_datetime_returns_structured_result(self):
        result = current_datetime("Need today's date", structured=True)

        self.assertTrue(result["success"])
        self.assertEqual(result["input"], "Need today's date")
        self.assertIn("UTC:", result["preview"])
        self.assertIn("weekday", {key.lower() for key in result["raw_output"].keys()})