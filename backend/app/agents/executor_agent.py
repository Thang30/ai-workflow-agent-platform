import json
import re
from typing import Any

from app.agents.prompts import (
    DEFAULT_EXECUTOR_DECISION_PROMPT,
    DEFAULT_EXECUTOR_RESPONSE_PROMPT,
    EXECUTOR_DECISION_PROMPT_KEY,
    EXECUTOR_RESPONSE_PROMPT_KEY,
    render_prompt,
    resolve_prompt,
)
from app.core.llm import LLMClient
from app.tools.common import build_tool_response, utc_now_iso
from app.tools.registry import DEFAULT_TOOL_REGISTRY, ToolDefinition


def _build_tool_query(query: str) -> str:
    if "Current step:" in query:
        return query.split("Current step:", 1)[1].strip()

    return query.strip()


class ExecutorAgent:
    def __init__(
        self,
        model: str | None = None,
        prompt_overrides: dict[str, str] | None = None,
        tools: dict[str, ToolDefinition] | None = None,
    ):
        self.llm = LLMClient(model=model)
        self.prompt_overrides = prompt_overrides or {}
        self.tools = tools or DEFAULT_TOOL_REGISTRY

    def _clean_json(self, text: str) -> str:
        return text.strip().replace("```json", "").replace("```", "")

    def _normalize_json(self, text: str) -> str:
        return re.sub(r",(\s*[\]}])", r"\1", text)

    def _extract_decision(self, text: str) -> dict:
        cleaned_text = self._clean_json(text)
        decoder = json.JSONDecoder()

        for index, char in enumerate(cleaned_text):
            if char != "{":
                continue

            candidate = cleaned_text[index:]

            try:
                parsed, _ = decoder.raw_decode(candidate)
            except json.JSONDecodeError:
                try:
                    parsed, _ = decoder.raw_decode(self._normalize_json(candidate))
                except json.JSONDecodeError:
                    continue

            if isinstance(parsed, dict):
                return parsed

        raise ValueError("No valid JSON decision object found in model response")

    def _format_available_tools(self) -> str:
        return "\n".join(
            f"- {tool.key}: {tool.description}" for tool in self.tools.values()
        )

    def _build_tool_entry(
        self,
        tool: ToolDefinition,
        tool_result: dict,
        decision_reason: str | None,
    ) -> dict:
        return {
            "name": tool.display_name,
            "input": tool_result.get("input", ""),
            "query": tool_result.get("query", tool_result.get("input", "")),
            "preview": tool_result.get("preview", ""),
            "raw_output": tool_result.get("raw_output"),
            "success": tool_result.get("success", False),
            "error_message": tool_result.get("error_message"),
            "started_at": tool_result.get("started_at"),
            "finished_at": tool_result.get("finished_at"),
            "duration_ms": tool_result.get("duration_ms"),
            "reason": decision_reason,
        }

    def _build_dispatch_failure(
        self,
        tool_name: str,
        tool_input: Any,
        error_message: str,
        decision_reason: str | None,
    ) -> dict:
        now = utc_now_iso()
        tool_result = build_tool_response(
            tool_input=tool_input,
            raw_output={"error": error_message},
            started_at=now,
            finished_at=now,
            elapsed_seconds=0,
            preview=error_message,
            success=False,
            error_message=error_message,
        )
        return {
            "name": tool_name,
            "input": tool_result["input"],
            "query": tool_result["query"],
            "preview": tool_result["preview"],
            "raw_output": tool_result["raw_output"],
            "success": tool_result["success"],
            "error_message": tool_result["error_message"],
            "started_at": tool_result["started_at"],
            "finished_at": tool_result["finished_at"],
            "duration_ms": tool_result["duration_ms"],
            "reason": decision_reason,
        }

    def _render_response(
        self,
        query: str,
        *,
        decision_reason: str,
        tool_name: str,
        tool_status: str,
        tool_preview: str,
    ) -> str:
        final_prompt = render_prompt(
            resolve_prompt(
                self.prompt_overrides,
                EXECUTOR_RESPONSE_PROMPT_KEY,
                DEFAULT_EXECUTOR_RESPONSE_PROMPT,
            ),
            query=query,
            decision_reason=decision_reason,
            tool_name=tool_name,
            tool_status=tool_status,
            tool_preview=tool_preview,
        )
        return self.llm.chat(final_prompt)

    def _resolve_tool_input(self, decision_input: Any, fallback_query: str) -> Any:
        if decision_input is None:
            return fallback_query

        if isinstance(decision_input, str):
            stripped = decision_input.strip()
            return stripped or fallback_query

        return decision_input

    def execute(self, query: str) -> dict:
        """
        Executes a workflow step and returns the answer with any tool metadata.
        """

        prompt = render_prompt(
            resolve_prompt(
                self.prompt_overrides,
                EXECUTOR_DECISION_PROMPT_KEY,
                DEFAULT_EXECUTOR_DECISION_PROMPT,
            ),
            query=query,
            available_tools=self._format_available_tools(),
        )

        raw_decision = self.llm.chat(prompt)
        fallback_query = _build_tool_query(query)

        try:
            decision = self._extract_decision(raw_decision)
        except ValueError:
            return {
                "output": self._render_response(
                    query,
                    decision_reason="The tool-selection response was invalid JSON, so no tool was used.",
                    tool_name="None",
                    tool_status="not_used",
                    tool_preview="No tool used.",
                ),
                "tools": [],
            }

        action = str(decision.get("action") or "respond").strip().lower()
        decision_reason = str(decision.get("reason") or "No rationale provided.").strip()

        if action != "use_tool":
            return {
                "output": self._render_response(
                    query,
                    decision_reason=decision_reason,
                    tool_name="None",
                    tool_status="not_used",
                    tool_preview="No tool used.",
                ),
                "tools": [],
            }

        tool_name = str(decision.get("tool_name") or "").strip().lower()
        tool_input = self._resolve_tool_input(decision.get("tool_input"), fallback_query)
        tool = self.tools.get(tool_name)

        if tool is None:
            failed_tool = self._build_dispatch_failure(
                tool_name or "Unknown tool",
                tool_input,
                f"Unknown tool requested: {tool_name or 'missing tool name'}",
                decision_reason,
            )
            return {
                "output": self._render_response(
                    query,
                    decision_reason=decision_reason,
                    tool_name=failed_tool["name"],
                    tool_status="failure",
                    tool_preview=failed_tool["preview"],
                ),
                "tools": [failed_tool],
            }

        try:
            tool_result = tool.handler(tool_input, structured=True)
            if not isinstance(tool_result, dict):
                raise ValueError("Tool did not return a structured result")
            tool_entry = self._build_tool_entry(tool, tool_result, decision_reason)
        except Exception as exc:
            tool_entry = self._build_dispatch_failure(
                tool.display_name,
                tool_input,
                f"Tool dispatch failed: {exc}",
                decision_reason,
            )

        return {
            "output": self._render_response(
                query,
                decision_reason=decision_reason,
                tool_name=tool_entry["name"],
                tool_status=("success" if tool_entry["success"] else "failure"),
                tool_preview=tool_entry["preview"],
            ),
            "tools": [tool_entry],
        }

    def run(self, query: str) -> str:
        """
        Uses LLM to decide how to respond
        """

        return self.execute(query)["output"]
