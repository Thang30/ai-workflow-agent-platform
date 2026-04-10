# Simple web search tool (mock version for now)
# Why mock first?
# - faster iteration
# - no API keys yet
# - focus on agent logic
#
#  Good move: reduce external dependencies early

def web_search(query: str) -> str:
    """
    Simulates a web search.
    Replace later with real API (Tavily, SerpAPI, etc.)
    """
    return f"Mock search results for: {query}"