from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.tools.calculator import calculate_expression
from app.tools.current_datetime import current_datetime
from app.tools.web_search import web_search

ToolHandler = Callable[[Any, bool], str | dict[str, Any]]


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    key: str
    display_name: str
    description: str
    handler: ToolHandler


DEFAULT_TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "web_search": ToolDefinition(
        key="web_search",
        display_name="Web Search",
        description="Search the web for current events, external facts, or information not present in the workflow context.",
        handler=web_search,
    ),
    "calculator": ToolDefinition(
        key="calculator",
        display_name="Calculator",
        description="Use for direct arithmetic and generic numeric expressions when no external lookup or time-aware context is needed.",
        handler=calculate_expression,
    ),
    "current_datetime": ToolDefinition(
        key="current_datetime",
        display_name="Current Date/Time",
        description="Return the current local and UTC date and time for date-aware answers, relative time questions, or scheduling context.",
        handler=current_datetime,
    ),
}
