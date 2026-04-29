from app.agents.prompts import (
    DEFAULT_EXECUTOR_DECISION_PROMPT,
    DEFAULT_EXECUTOR_RESPONSE_PROMPT,
    EXECUTOR_DECISION_PROMPT_KEY,
    EXECUTOR_RESPONSE_PROMPT_KEY,
    render_prompt,
    resolve_prompt,
)
from app.core.llm import LLMClient
from app.tools.web_search import web_search


def _build_tool_query(query: str) -> str:
    if "Current step:" in query:
        return query.split("Current step:", 1)[1].strip()

    return query.strip()


class ExecutorAgent:
    def __init__(
        self,
        model: str | None = None,
        prompt_overrides: dict[str, str] | None = None,
    ):
        self.llm = LLMClient(model=model)
        self.prompt_overrides = prompt_overrides or {}

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
        )

        decision = self.llm.chat(prompt)

        if "USE_TOOL" in decision:
            tool_query = _build_tool_query(query)
            tool_result = web_search(tool_query, structured=True)

            final_prompt = render_prompt(
                resolve_prompt(
                    self.prompt_overrides,
                    EXECUTOR_RESPONSE_PROMPT_KEY,
                    DEFAULT_EXECUTOR_RESPONSE_PROMPT,
                ),
                query=query,
                tool_status=("success" if tool_result["success"] else "failure"),
                tool_preview=tool_result["preview"],
            )
            return {
                "output": self.llm.chat(final_prompt),
                "tools": [
                    {
                        "name": "Web Search",
                        "query": tool_result["query"],
                        "preview": tool_result["preview"],
                        "raw_output": tool_result["raw_output"],
                        "success": tool_result["success"],
                        "error_message": tool_result["error_message"],
                        "started_at": tool_result["started_at"],
                        "finished_at": tool_result["finished_at"],
                        "duration_ms": tool_result["duration_ms"],
                    }
                ],
            }

        return {"output": decision, "tools": []}

    def run(self, query: str) -> str:
        """
        Uses LLM to decide how to respond
        """

        return self.execute(query)["output"]
