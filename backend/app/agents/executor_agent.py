from app.core.llm import LLMClient
from app.tools.web_search import web_search


def _build_tool_query(query: str) -> str:
    if "Current step:" in query:
        return query.split("Current step:", 1)[1].strip()

    return query.strip()


class ExecutorAgent:
    def __init__(self):
        self.llm = LLMClient()

    def execute(self, query: str) -> dict:
        """
        Executes a workflow step and returns the answer with any tool metadata.
        """

        prompt = f"""
You are an AI assistant.

If the user asks to search or find information,
you should say: USE_TOOL

Otherwise respond normally.

User query: {query}
"""

        decision = self.llm.chat(prompt)

        if "USE_TOOL" in decision:
            tool_query = _build_tool_query(query)
            tool_result = web_search(tool_query, structured=True)

            final_prompt = f"""
User query: {query}

Tool result:
{tool_result["preview"]}

Generate final answer.
"""
            return {
                "output": self.llm.chat(final_prompt),
                "tools": [
                    {
                        "name": "Web Search",
                        "query": tool_result["query"],
                        "preview": tool_result["preview"],
                        "raw_output": tool_result["raw_output"],
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
