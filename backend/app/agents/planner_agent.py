import json
import re

from app.agents.prompts import (
    DEFAULT_PLANNER_PROMPT,
    PLANNER_PROMPT_KEY,
    render_prompt,
    resolve_prompt,
)
from app.core.llm import LLMClient


class PlannerAgent:
    def __init__(
        self,
        model: str | None = None,
        prompt_overrides: dict[str, str] | None = None,
    ):
        self.llm = LLMClient(model=model)
        self.prompt_overrides = prompt_overrides or {}

    def _clean_json(self, text: str) -> str:
        return text.strip().replace("```json", "").replace("```", "")

    def _normalize_json(self, text: str) -> str:
        return re.sub(r",(\s*[\]}])", r"\1", text)

    def _extract_steps(self, text: str):
        cleaned_text = self._clean_json(text)
        decoder = json.JSONDecoder()

        for index, char in enumerate(cleaned_text):
            if char not in "[{":
                continue

            candidate = cleaned_text[index:]

            try:
                parsed, _ = decoder.raw_decode(candidate)
            except json.JSONDecodeError:
                try:
                    parsed, _ = decoder.raw_decode(self._normalize_json(candidate))
                except json.JSONDecodeError:
                    continue

            if isinstance(parsed, list):
                return parsed

        raise ValueError("No valid JSON step list found in model response")

    def _build_fallback_steps(self, query: str):
        return [{"step": 1, "description": query}]

    def run(self, query: str, improvement_hint: str | None = None):
        """
        Generates a step-by-step plan from user query.
        Returns a list of steps.
        """
        retry_guidance = ""
        if improvement_hint:
            retry_guidance = (
                "\nAdditional retry guidance from the previous attempt:\n"
                f"{improvement_hint}\n"
                "Revise the plan to directly address these issues.\n"
            )

        prompt = render_prompt(
            resolve_prompt(
                self.prompt_overrides,
                PLANNER_PROMPT_KEY,
                DEFAULT_PLANNER_PROMPT,
            ),
            query=query,
            retry_guidance=retry_guidance,
        )

        response = self.llm.chat(prompt)

        try:
            return self._extract_steps(response)
        except Exception:
            return self._build_fallback_steps(query)
