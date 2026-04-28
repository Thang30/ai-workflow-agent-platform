from tavily import TavilyClient

try:
    from app.core.config import settings
except ImportError:
    from core.config import settings


def web_search(query: str) -> str:
    if not settings.tavily_api_key:
        raise ValueError("TAVILY_API_KEY is not configured")

    client = TavilyClient(api_key=settings.tavily_api_key)
    results = client.search(query=query)
    print("Web search raw results:", results)

    return "\n".join([r["content"] for r in results["results"][:3]])
