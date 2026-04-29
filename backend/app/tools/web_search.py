from time import perf_counter
from typing import Any

from tavily import TavilyClient

from app.tools.common import build_tool_response, utc_now_iso

try:
    from app.core.config import settings
except ImportError:
    from core.config import settings


MAX_SEARCH_QUERY_LENGTH = 400


def _normalize_query(query: str) -> str:
    return " ".join(query.split())[:MAX_SEARCH_QUERY_LENGTH]


def _format_preview(results: dict[str, Any]) -> str:
    return "\n".join(item["content"] for item in results.get("results", [])[:3])


def _build_structured_response(
    *,
    tool_input: str,
    raw_output: dict[str, Any],
    preview: str,
    success: bool,
    error_message: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
    elapsed_seconds: float = 0,
) -> dict[str, Any]:
    timestamp = started_at or utc_now_iso()
    return build_tool_response(
        tool_input=tool_input,
        raw_output=raw_output,
        started_at=timestamp,
        finished_at=finished_at or timestamp,
        elapsed_seconds=elapsed_seconds,
        preview=preview,
        success=success,
        error_message=error_message,
    )


def web_search(query: str, structured: bool = False) -> str | dict[str, Any]:
    if not settings.tavily_api_key:
        error_message = "Web search unavailable: TAVILY_API_KEY is not configured"
        if structured:
            return _build_structured_response(
                tool_input=_normalize_query(query),
                raw_output={"error": "TAVILY_API_KEY is not configured"},
                preview=error_message,
                success=False,
                error_message="TAVILY_API_KEY is not configured",
            )

        raise ValueError("TAVILY_API_KEY is not configured")

    normalized_query = _normalize_query(query)
    if not normalized_query:
        empty_message = "Web search unavailable: empty query"
        if structured:
            return _build_structured_response(
                tool_input=normalized_query,
                raw_output={"results": []},
                preview=empty_message,
                success=False,
                error_message="Empty query",
            )

        return empty_message

    client = TavilyClient(api_key=settings.tavily_api_key)
    started_at = utc_now_iso()
    started_at_monotonic = perf_counter()

    try:
        results = client.search(query=normalized_query)
    except Exception as exc:
        error_message = f"Web search unavailable: {exc}"
        if structured:
            return _build_structured_response(
                tool_input=normalized_query,
                raw_output={"error": str(exc)},
                started_at=started_at,
                finished_at=utc_now_iso(),
                elapsed_seconds=perf_counter() - started_at_monotonic,
                preview=error_message,
                success=False,
                error_message=str(exc),
            )

        return error_message

    preview = _format_preview(results)
    if structured:
        return _build_structured_response(
            tool_input=normalized_query,
            raw_output=results,
            started_at=started_at,
            finished_at=utc_now_iso(),
            elapsed_seconds=perf_counter() - started_at_monotonic,
            preview=preview,
            success=True,
        )

    return preview
