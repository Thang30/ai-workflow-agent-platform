# Executor Agent
# Responsible for:
# - Taking input from the user
# - Using tools when needed
# - Returning a response

from app.tools.web_search import web_search


class ExecutorAgent:
    def __init__(self):
        pass

    def run(self, query: str) -> str:
        """
        Executes a user query using available tools.

        Steps:
        1. Decide if tool is needed
        2. Call tool
        3. Return formatted response
        """
        # TODO: replace with LLM-based decision later

        if "search" in query.lower() or "find" in query.lower():
            result = web_search(query)
            return f"Used web search tool:\n{result}"

        return f"Direct response: {query}"