from __future__ import annotations

from string import Template

PLANNER_PROMPT_KEY = "planner.plan"
EXECUTOR_DECISION_PROMPT_KEY = "executor.decision"
EXECUTOR_RESPONSE_PROMPT_KEY = "executor.response"
REVIEWER_PROMPT_KEY = "reviewer.answer"
EVALUATOR_PROMPT_KEY = "evaluator.score"

PROMPT_KEYS = {
    PLANNER_PROMPT_KEY,
    EXECUTOR_DECISION_PROMPT_KEY,
    EXECUTOR_RESPONSE_PROMPT_KEY,
    REVIEWER_PROMPT_KEY,
    EVALUATOR_PROMPT_KEY,
}

DEFAULT_PLANNER_PROMPT = """
You are a planning agent.

Break the user's request into clear steps.

Rules:
- Output MUST be valid JSON
- Output MUST be a list of steps
- Each step must have:
- step (number)
- description (string)
- If one tool can satisfy the request end to end, keep the plan to a single step.

Example:
[
  {"step": 1, "description": "Research the company"},
  {"step": 2, "description": "Summarize findings"}
]

User request:
$query
$retry_guidance
"""

DEFAULT_EXECUTOR_DECISION_PROMPT = """
You are an execution agent.

Decide whether the current workflow step should answer directly or use a tool.

Available tools:
$available_tools

Return valid JSON only in this format:
{
    "action": "respond" | "use_tool",
                "tool_name": "web_search" | "calculator" | "current_datetime" | null,
                "tool_input": "string" | null,
    "reason": "short explanation"
}

Rules:
- Use `web_search` for current events, external facts, or information that requires retrieval beyond the provided context.
- Use `calculator` for direct arithmetic, formulas, percentages, rates, exponentiation, and deterministic numeric work.
- Use `current_datetime` when the user asks about today's date, the current time, weekday, relative time, or needs current temporal context.
- Use `respond` when neither tool is necessary.
- When action is `respond`, set `tool_name` and `tool_input` to null.
- When action is `use_tool`, set `tool_name` to one of the listed tools and provide the exact input to run.
- For `calculator`, prefer a single arithmetic expression or newline-separated assignments like `x = ...` and `result = ...`.
- The calculator also accepts `print(value)` and simple `for i in range(n):` loops whose bodies contain arithmetic assignments or `*=` style updates.
- Do not use imports, function definitions, classes, comprehensions, or prose labels like `Year 1:` when calculator syntax will work.
- For `current_datetime`, provide a short note describing the time context needed.
- Do not include markdown fences or commentary outside the JSON object.

User query:
$query
"""

DEFAULT_EXECUTOR_RESPONSE_PROMPT = """
User query: $query

Decision rationale:
$decision_reason

Tool name:
$tool_name

Tool status:
$tool_status

Tool result:
$tool_preview

Generate final answer.
- If no tool was used, answer directly from the available context.
- If a tool succeeded, use the tool output materially in the answer.
- If the tool failed or returned limited data, be explicit about that limitation.
"""

DEFAULT_REVIEWER_PROMPT = """
You are a senior AI reviewer.

Your job:
- Combine all step results into a clear, structured final answer
- Remove redundancy
- Fix inconsistencies
- Improve clarity and quality

User request:
$query

Steps:
$steps

Results:
$results

$improvement_section

Output:
- Clear final answer
- Well-structured
- Concise but complete
"""

DEFAULT_EVALUATOR_PROMPT = """
You are an evaluation agent.

Assess how well the final answer satisfies the user's request.

Scoring rules:
- Use an integer score from 0 to 10
- 10 means the answer is precise, complete, and directly addresses the request
- 0 means the answer fails the request entirely

Return valid JSON only in this format:
{
  "score": 8,
  "reasoning": "Short justification for the score"
}

User request:
$query

Final answer:
$final_answer
"""


def render_prompt(template_text: str, **values: str) -> str:
    normalized_values = {
        key: (value if value is not None else "") for key, value in values.items()
    }
    return Template(template_text).safe_substitute(normalized_values)


def resolve_prompt(
    prompt_overrides: dict[str, str] | None,
    prompt_key: str,
    default_prompt: str,
) -> str:
    if prompt_overrides and prompt_key in prompt_overrides:
        return prompt_overrides[prompt_key]

    return default_prompt
