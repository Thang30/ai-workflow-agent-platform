from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from app.tools.common import build_tool_response, utc_now_iso


def current_datetime(tool_input: Any, structured: bool = False) -> str | dict[str, Any]:
    started_at = utc_now_iso()
    started_at_monotonic = perf_counter()
    local_now = datetime.now().astimezone()
    utc_now = datetime.now(timezone.utc)

    raw_output: dict[str, Any] = {
        "local_iso": local_now.isoformat(),
        "local_date": local_now.date().isoformat(),
        "local_time": local_now.strftime("%H:%M:%S"),
        "local_timezone": str(local_now.tzinfo),
        "utc_iso": utc_now.isoformat().replace("+00:00", "Z"),
        "weekday": local_now.strftime("%A"),
    }
    preview = (
        f"Local: {raw_output['local_iso']}\n"
        f"UTC: {raw_output['utc_iso']}\n"
        f"Weekday: {raw_output['weekday']}"
    )
    result = build_tool_response(
        tool_input=tool_input or "current date and time",
        raw_output=raw_output,
        started_at=started_at,
        finished_at=utc_now_iso(),
        elapsed_seconds=perf_counter() - started_at_monotonic,
        preview=preview,
        success=True,
    )
    if structured:
        return result

    return result["preview"]