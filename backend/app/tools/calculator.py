from __future__ import annotations

import ast
import math
import re
from time import perf_counter
from typing import Any, Callable

from app.tools.common import build_tool_response, truncate_tool_text, utc_now_iso


ALLOWED_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "abs": abs,
    "ceil": math.ceil,
    "exp": math.exp,
    "floor": math.floor,
    "len": len,
    "log": math.log,
    "log10": math.log10,
    "max": max,
    "min": min,
    "pow": pow,
    "round": round,
    "sqrt": math.sqrt,
    "sum": sum,
}

ALLOWED_CONSTANTS: dict[str, float] = {
    "e": math.e,
    "pi": math.pi,
    "tau": math.tau,
}

MAX_RANGE_ITERATIONS = 1000
LABELED_LINE_PATTERN = re.compile(
    r"^(?P<indent>\s*)(?P<label>[A-Za-z][A-Za-z0-9 _-]*):\s*(?P<expr>.+)$"
)


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"

    if isinstance(value, list):
        return "[" + ", ".join(_format_value(item) for item in value) + "]"

    if isinstance(value, tuple):
        return "(" + ", ".join(_format_value(item) for item in value) + ")"

    return str(value)


def _json_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]

    if isinstance(value, list):
        return [_json_value(item) for item in value]

    return value


def _sanitize_label(label: str) -> str:
    sanitized = re.sub(r"[^0-9A-Za-z]+", "_", label.strip().lower()).strip("_")
    if not sanitized:
        return "value"

    if sanitized[0].isdigit():
        return f"value_{sanitized}"

    return sanitized


def _normalize_expression(expression: str) -> str:
    normalized_lines: list[str] = []

    for raw_line in expression.splitlines():
        if not raw_line.strip():
            continue

        match = LABELED_LINE_PATTERN.match(raw_line)
        if match:
            label = match.group("label").strip().lower()
            if not label.startswith(("for ", "if ", "while ", "elif ", "else")):
                normalized_lines.append(
                    f"{match.group('indent')}{_sanitize_label(match.group('label'))} = {match.group('expr').strip()}"
                )
                continue

        normalized_lines.append(raw_line)

    return "\n".join(normalized_lines).replace("^", "**")


class CalculatorEvaluator:
    def __init__(self):
        self.variables: dict[str, Any] = {}

    def evaluate(self, expression: str) -> tuple[list[dict[str, Any]], Any]:
        parsed = ast.parse(_normalize_expression(expression), mode="exec")
        if not parsed.body:
            raise ValueError("Calculator input is empty")

        results: list[dict[str, Any]] = []
        last_value: Any = None

        for statement in parsed.body:
            statement_results, last_value = self._execute_statement(statement)
            results.extend(statement_results)

        return results, last_value

    def _execute_statement(
        self,
        statement: ast.stmt,
    ) -> tuple[list[dict[str, Any]], Any]:
        if isinstance(statement, ast.Assign):
            if len(statement.targets) != 1 or not isinstance(
                statement.targets[0], ast.Name
            ):
                raise ValueError("Calculator only supports single variable assignments")

            variable_name = statement.targets[0].id
            value = self._eval_node(statement.value)
            self.variables[variable_name] = value
            return (
                [
                    {
                        "type": "assignment",
                        "name": variable_name,
                        "value": _json_value(value),
                        "display": f"{variable_name} = {_format_value(value)}",
                    }
                ],
                value,
            )

        if isinstance(statement, ast.AugAssign):
            if not isinstance(statement.target, ast.Name):
                raise ValueError("Calculator only supports variable augmented assignments")

            variable_name = statement.target.id
            current_value = self._eval_node(statement.target)
            next_value = self._apply_operator(
                current_value,
                self._eval_node(statement.value),
                statement.op,
            )
            self.variables[variable_name] = next_value
            return (
                [
                    {
                        "type": "assignment",
                        "name": variable_name,
                        "value": _json_value(next_value),
                        "display": f"{variable_name} = {_format_value(next_value)}",
                    }
                ],
                next_value,
            )

        if isinstance(statement, ast.Expr):
            value = self._eval_node(statement.value)
            return (
                [
                    {
                        "type": "expression",
                        "name": None,
                        "value": _json_value(value),
                        "display": _format_value(value),
                    }
                ],
                value,
            )

        if isinstance(statement, ast.For):
            if statement.orelse:
                raise ValueError("Calculator loops do not support else blocks")
            if not isinstance(statement.target, ast.Name):
                raise ValueError("Calculator only supports simple range loops")

            loop_results: list[dict[str, Any]] = []
            last_value: Any = None
            for loop_value in self._evaluate_range(statement.iter):
                self.variables[statement.target.id] = loop_value
                for body_statement in statement.body:
                    body_results, last_value = self._execute_statement(body_statement)
                    loop_results.extend(body_results)

            return loop_results, last_value

        raise ValueError(
            "Calculator only supports arithmetic expressions, simple assignments, and range loops"
        )

    def _evaluate_range(self, node: ast.AST) -> range:
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            raise ValueError("Calculator loops only support range(...)")
        if node.func.id != "range":
            raise ValueError("Calculator loops only support range(...)")
        if node.keywords:
            raise ValueError("Calculator range(...) does not support keyword arguments")
        if not 1 <= len(node.args) <= 3:
            raise ValueError("Calculator range(...) supports 1 to 3 positional arguments")

        values = [self._coerce_int(self._eval_node(argument)) for argument in node.args]
        result = range(*values)
        if len(result) > MAX_RANGE_ITERATIONS:
            raise ValueError(
                f"Calculator loops are limited to {MAX_RANGE_ITERATIONS} iterations"
            )

        return result

    def _coerce_int(self, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Calculator range(...) arguments must be numeric")
        if int(value) != value:
            raise ValueError("Calculator range(...) arguments must be whole numbers")

        return int(value)

    def _apply_operator(self, left: Any, right: Any, operator: ast.AST) -> Any:
        if isinstance(operator, ast.Add):
            return left + right
        if isinstance(operator, ast.Sub):
            return left - right
        if isinstance(operator, ast.Mult):
            return left * right
        if isinstance(operator, ast.Div):
            return left / right
        if isinstance(operator, ast.FloorDiv):
            return left // right
        if isinstance(operator, ast.Mod):
            return left % right
        if isinstance(operator, ast.Pow):
            return left**right
        raise ValueError("Unsupported calculator operation")

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Calculator only supports numeric constants")

        if isinstance(node, ast.Name):
            if node.id in self.variables:
                return self.variables[node.id]
            if node.id in ALLOWED_CONSTANTS:
                return ALLOWED_CONSTANTS[node.id]
            if node.id in ALLOWED_FUNCTIONS:
                return ALLOWED_FUNCTIONS[node.id]
            raise ValueError(f"Unknown symbol: {node.id}")

        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self._apply_operator(left, right, node.op)

        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)

            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            raise ValueError("Unsupported unary operation")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Unsupported function call")

            function_name = node.func.id
            if function_name == "print":
                if node.keywords:
                    raise ValueError("Keyword arguments are not supported")
                values = [self._eval_node(arg) for arg in node.args]
                if not values:
                    raise ValueError("print() requires at least one argument")
                return values[0] if len(values) == 1 else values

            function = ALLOWED_FUNCTIONS.get(function_name)
            if function is None:
                raise ValueError(f"Unsupported function: {function_name}")

            if node.keywords:
                raise ValueError("Keyword arguments are not supported")

            return function(*[self._eval_node(arg) for arg in node.args])

        if isinstance(node, ast.List):
            return [self._eval_node(item) for item in node.elts]

        if isinstance(node, ast.Tuple):
            return tuple(self._eval_node(item) for item in node.elts)

        raise ValueError("Unsupported calculator syntax")


def calculate_expression(expression: str, structured: bool = False) -> str | dict[str, Any]:
    normalized_expression = expression.strip()
    started_at = utc_now_iso()
    started_at_monotonic = perf_counter()

    if not normalized_expression:
        result = build_tool_response(
            tool_input=expression,
            raw_output={"results": [], "variables": {}, "final_value": None},
            started_at=started_at,
            finished_at=started_at,
            elapsed_seconds=0,
            preview="Calculator unavailable: empty expression",
            success=False,
            error_message="Empty expression",
        )
        if structured:
            return result

        return result["preview"]

    try:
        evaluator = CalculatorEvaluator()
        results, last_value = evaluator.evaluate(normalized_expression)
    except Exception as exc:
        preview = truncate_tool_text(
            f"Calculator error: {exc}",
            4000,
        )
        result = build_tool_response(
            tool_input=expression,
            raw_output={"results": [], "variables": {}, "final_value": None},
            started_at=started_at,
            finished_at=utc_now_iso(),
            elapsed_seconds=perf_counter() - started_at_monotonic,
            preview=preview,
            success=False,
            error_message=str(exc),
        )
        if structured:
            return result

        return result["preview"]

    preview = truncate_tool_text(
        "\n".join(result["display"] for result in results),
        4000,
    )
    result = build_tool_response(
        tool_input=expression,
        raw_output={
            "results": results,
            "variables": {
                key: _json_value(value) for key, value in evaluator.variables.items()
            },
            "final_value": _json_value(last_value),
        },
        started_at=started_at,
        finished_at=utc_now_iso(),
        elapsed_seconds=perf_counter() - started_at_monotonic,
        preview=preview,
        success=True,
    )
    if structured:
        return result

    return result["preview"]