from tavily import TavilyClient

try:
    from app.core.config import settings
except ImportError:
    from core.config import settings


MAX_SEARCH_QUERY_LENGTH = 400


def _normalize_query(query: str) -> str:
    return " ".join(query.split())[:MAX_SEARCH_QUERY_LENGTH]


def web_search(query: str) -> str:
    if not settings.tavily_api_key:
        raise ValueError("TAVILY_API_KEY is not configured")

    normalized_query = _normalize_query(query)
    if not normalized_query:
        return "Web search unavailable: empty query"

    client = TavilyClient(api_key=settings.tavily_api_key)
    try:
        results = client.search(query=normalized_query)
    except Exception as exc:
        return f"Web search unavailable: {exc}"

    print("Web search raw results:", results)

    return "\n".join([r["content"] for r in results["results"][:3]])
