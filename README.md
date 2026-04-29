# ai-workflow-agent-platform

A multi-agent system that completes real workflows with visible reasoning, tools, and structure.

## Tool execution

The executor now selects between multiple tools at runtime instead of relying on a single hardcoded search path.

- `web_search` is used for current events, external facts, and retrieval-heavy steps.
- `calculator` is used for deterministic formulas, arithmetic, and numeric tasks.
- `current_datetime` is used for current date and time context.
- Tool choice happens inside the executor. The planner output remains step-oriented and tool-agnostic.

## Config-driven experiments

The active A/B test is now configured in the backend `.env` instead of being created from the UI.

Start from [backend/.env.example](/Users/thang.ngo/AI-projects/ai-workflow-agent-platform/ai-workflow-agent-platform/backend/.env.example). Prompt file paths are resolved relative to `backend/`.

Model split:

```env
EXPERIMENT_ENABLED=true
EXPERIMENT_NAME=model-comparison-apr-2026
EXPERIMENT_TYPE=model
EXPERIMENT_VARIANT_A_NAME=A
EXPERIMENT_VARIANT_A_MODEL=meta-llama/Llama-3.1-8B-Instruct:cheapest
EXPERIMENT_VARIANT_B_NAME=B
EXPERIMENT_VARIANT_B_MODEL=openai/gpt-oss-120b:cerebras
```

Planner prompt split:

```env
EXPERIMENT_ENABLED=true
EXPERIMENT_NAME=planner-prompt-apr-2026
EXPERIMENT_TYPE=prompt
EXPERIMENT_VARIANT_A_NAME=A
EXPERIMENT_VARIANT_A_PLANNER_PROMPT_FILE=prompts/experiments/planner-variant-a.txt
EXPERIMENT_VARIANT_B_NAME=B
EXPERIMENT_VARIANT_B_PLANNER_PROMPT_FILE=prompts/experiments/planner-variant-b.txt
```

Notes:

- Only one active experiment is supported at a time.
- Prompt experiments only target the planner prompt.
- Keep the experiment name and variant definitions immutable while it is active so analytics stay comparable.
- Live workflow, run history, and analytics will show the assigned variant automatically.
- Inline planner prompt env vars still work, but prompt files are easier to review and diff.
