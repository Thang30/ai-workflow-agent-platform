from app.core.llm import LLMClient
from app.tools.web_search import web_search

class ExecutorAgent:
    def __init__(self):
        self.llm = LLMClient()

    def run(self, query: str) -> str:
        """
        Uses LLM to decide how to respond
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
            tool_result = web_search(query)

            final_prompt = f"""
User query: {query}

Tool result:
{tool_result}

Generate final answer.
"""
            return self.llm.chat(final_prompt)

        return decision