from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from tavily import TavilyClient

try:
    from app.core.config import settings
except ImportError:
    from core.config import settings


MAX_SEARCH_QUERY_LENGTH = 400


def _normalize_query(query: str) -> str:
    return " ".join(query.split())[:MAX_SEARCH_QUERY_LENGTH]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _format_preview(results: dict[str, Any]) -> str:
    return "\n".join([item["content"] for item in results.get("results", [])[:3]])


def _build_tool_response(
    query: str,
    raw_output: Any,
    started_at: str,
    finished_at: str,
    elapsed_seconds: float,
    preview: str,
) -> dict[str, Any]:
    return {
        "query": query,
        "preview": preview,
        "raw_output": raw_output,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": round(elapsed_seconds * 1000, 2),
    }


def web_search(query: str, structured: bool = False) -> str | dict[str, Any]:
    if not settings.tavily_api_key:
        raise ValueError("TAVILY_API_KEY is not configured")

    normalized_query = _normalize_query(query)
    if not normalized_query:
        empty_message = "Web search unavailable: empty query"
        if structured:
            now = _utc_now_iso()
            return _build_tool_response(
                query=normalized_query,
                raw_output={"results": []},
                started_at=now,
                finished_at=now,
                elapsed_seconds=0,
                preview=empty_message,
            )

        return empty_message

    client = TavilyClient(api_key=settings.tavily_api_key)
    started_at = _utc_now_iso()
    started_at_monotonic = perf_counter()

    try:
        results = client.search(query=normalized_query)
    except Exception as exc:
        error_message = f"Web search unavailable: {exc}"
        if structured:
            return _build_tool_response(
                query=normalized_query,
                raw_output={"error": str(exc)},
                started_at=started_at,
                finished_at=_utc_now_iso(),
                elapsed_seconds=perf_counter() - started_at_monotonic,
                preview=error_message,
            )

        return error_message

    print("Web search raw results:", results)

    preview = _format_preview(results)
    if structured:
        return _build_tool_response(
            query=normalized_query,
            raw_output=results,
            started_at=started_at,
            finished_at=_utc_now_iso(),
            elapsed_seconds=perf_counter() - started_at_monotonic,
            preview=preview,
        )

    return preview
