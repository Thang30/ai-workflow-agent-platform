from app.agents.prompts import (
    DEFAULT_REVIEWER_PROMPT,
    REVIEWER_PROMPT_KEY,
    render_prompt,
    resolve_prompt,
)
from app.core.llm import LLMClient


class ReviewerAgent:
    def __init__(
        self,
        model: str | None = None,
        prompt_overrides: dict[str, str] | None = None,
    ):
        self.llm = LLMClient(model=model)
        self.prompt_overrides = prompt_overrides or {}

    def run(
        self,
        query: str,
        steps: list,
        results: str,
        improvement_hint: str | None = None,
    ) -> str:
        """
        Reviews and synthesizes all step results into a final answer.
        """

        improvement_section = ""
        if improvement_hint:
            improvement_section = f"""
Retry guidance from the previous attempt:
{improvement_hint}

Address these issues directly in the final answer.
"""

        prompt = render_prompt(
            resolve_prompt(
                self.prompt_overrides,
                REVIEWER_PROMPT_KEY,
                DEFAULT_REVIEWER_PROMPT,
            ),
            query=query,
            steps=str(steps),
            results=results,
            improvement_section=improvement_section,
        )

        return self.llm.chat(prompt)
