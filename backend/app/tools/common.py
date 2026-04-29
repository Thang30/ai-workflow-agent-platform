import json
from datetime import datetime, timezone
from typing import Any

MAX_TOOL_INPUT_LENGTH = 4000
TRUNCATION_SUFFIX = "\n...[truncated]"


def normalize_tool_input(
    tool_input: Any, max_length: int = MAX_TOOL_INPUT_LENGTH
) -> str:
    if isinstance(tool_input, str):
        serialized_input = tool_input.strip()
    else:
        serialized_input = json.dumps(
            tool_input,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

    return serialized_input[:max_length]


def truncate_tool_text(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text

    if max_length <= len(TRUNCATION_SUFFIX):
        return TRUNCATION_SUFFIX[:max_length]

    return text[: max_length - len(TRUNCATION_SUFFIX)] + TRUNCATION_SUFFIX


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_tool_response(
    *,
    tool_input: Any,
    raw_output: Any,
    started_at: str,
    finished_at: str,
    elapsed_seconds: float,
    preview: str,
    success: bool,
    error_message: str | None = None,
) -> dict[str, Any]:
    normalized_input = normalize_tool_input(tool_input)
    return {
        "input": normalized_input,
        "query": normalized_input,
        "preview": preview,
        "raw_output": raw_output,
        "success": success,
        "error_message": error_message,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": round(elapsed_seconds * 1000, 2),
    }
