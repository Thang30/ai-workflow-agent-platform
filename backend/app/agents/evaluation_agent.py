import json
import re

from app.agents.prompts import (
    DEFAULT_EVALUATOR_PROMPT,
    EVALUATOR_PROMPT_KEY,
    render_prompt,
    resolve_prompt,
)
from app.core.llm import LLMClient


class EvaluationAgent:
    def __init__(
        self,
        model: str | None = None,
        prompt_overrides: dict[str, str] | None = None,
    ):
        self.llm = LLMClient(model=model)
        self.prompt_overrides = prompt_overrides or {}

    def _clean_json(self, text: str) -> str:
        return text.strip().replace("```json", "").replace("```", "")

    def _normalize_score(self, score) -> int:
        if isinstance(score, bool):
            return 1 if score else 0

        if isinstance(score, (int, float)):
            return max(0, min(10, int(round(score))))

        match = re.search(r"-?\d+(?:\.\d+)?", str(score))
        if not match:
            return 0

        return max(0, min(10, int(round(float(match.group(0))))))

    def _parse_response(self, response: str) -> dict:
        cleaned = self._clean_json(response)
        decoder = json.JSONDecoder()

        for index, char in enumerate(cleaned):
            if char != "{":
                continue

            candidate = cleaned[index:]

            try:
                parsed, _ = decoder.raw_decode(candidate)
            except json.JSONDecodeError:
                continue

            if not isinstance(parsed, dict) or "score" not in parsed:
                continue

            reasoning = str(parsed.get("reasoning", "")).strip()
            return {
                "score": self._normalize_score(parsed["score"]),
                "reasoning": reasoning or "The evaluator did not provide reasoning.",
            }

        return {
            "score": self._normalize_score(cleaned),
            "reasoning": cleaned or "The evaluator did not return structured output.",
        }

    def run(self, query: str, final_answer: str) -> dict:
        prompt = render_prompt(
            resolve_prompt(
                self.prompt_overrides,
                EVALUATOR_PROMPT_KEY,
                DEFAULT_EVALUATOR_PROMPT,
            ),
            query=query,
            final_answer=final_answer,
        )

        return self._parse_response(self.llm.chat(prompt))
