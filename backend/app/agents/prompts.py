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
You are an AI assistant.

If the user asks to search or find information,
you should say: USE_TOOL

Otherwise respond normally.

User query: $query
"""

DEFAULT_EXECUTOR_RESPONSE_PROMPT = """
User query: $query

Tool status:
$tool_status

Tool result:
$tool_preview

Generate final answer.
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
