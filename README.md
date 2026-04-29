# AI Workflow Agent Platform

AI Workflow Agent Platform is an inspectable multi-agent workflow system. It turns a user query into a plan, executes the steps with runtime tool selection, reviews the result into a final answer, evaluates quality, optionally retries, and persists the full run for history and analytics.

The focus is operational visibility: plans, step traces, tool metadata, attempts, evaluator feedback, and experiment-aware analytics. For deeper design context, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/SPEC_1.md](docs/SPEC_1.md).

## Overview

- `PlannerAgent` creates the step plan
- `ExecutorAgent` runs each step and selects tools at runtime
- `ReviewerAgent` synthesizes the final answer
- `EvaluationAgent` scores the answer on a 0-10 scale
- `WorkflowOrchestrator` handles retries, SSE, and persistence
- Frontend pages cover live workflow, run history, and analytics

Built-in tools:

- `web_search` for current external facts
- `calculator` for deterministic numeric work
- `current_datetime` for time-aware questions

## Workflow

1. Plan the request.
2. Execute each step and call tools when needed.
3. Review the intermediate results into the final answer.
4. Evaluate the answer.
5. Retry if the score is too low or a required tool failed.
6. Persist the selected attempt plus the full attempt history.

Only one active experiment is supported at a time, and each run can be assigned a model split or planner prompt variant.

## Quick start

Prerequisites:

- Python 3
- Node.js and npm
- PostgreSQL
- Hugging Face API token
- Optional Tavily API key for web search

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Minimum `backend/.env` values:

```env
DATABASE_URL=postgresql://localhost:5432/ai_workflow_agent_platform
HF_TOKEN=replace-with-your-hugging-face-token
MODEL=meta-llama/Llama-3.1-8B-Instruct:cheapest
TAVILY_API_KEY=
```

### Frontend

Create `frontend/ai-workflow-agent-platform-frontend/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

Start the frontend:

```bash
cd frontend/ai-workflow-agent-platform-frontend
npm install
npm run dev
```

Local URLs:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## Configuration

Required environment variables:

- `DATABASE_URL` for PostgreSQL persistence
- `HF_TOKEN` for model access through `huggingface_hub`
- `MODEL` as the default model for planner, executor, reviewer, and evaluator

Common optional variables:

- `TAVILY_API_KEY` to enable `web_search`
- `SELF_IMPROVEMENT_LOW_SCORE_THRESHOLD` and `SELF_IMPROVEMENT_MAX_RETRIES` to tune retries
- `FRONTEND_ORIGINS` and `FRONTEND_ORIGIN_REGEX` to adjust CORS
- `EXPERIMENT_*` to activate one model or planner prompt split

Notes:

- `postgres://` and `postgresql://` URLs are normalized automatically for SQLAlchemy + psycopg.
- If Tavily is not configured, search-dependent steps degrade gracefully and record tool failure metadata.

## Experiments

Experiments are configured in `backend/.env` and assigned per run.

Model split:

```env
EXPERIMENT_ENABLED=true
EXPERIMENT_NAME=model-comparison-apr-2026
EXPERIMENT_TYPE=model
EXPERIMENT_VARIANT_A_MODEL=meta-llama/Llama-3.1-8B-Instruct:cheapest
EXPERIMENT_VARIANT_B_MODEL=openai/gpt-oss-120b:cerebras
```

Planner prompt split:

```env
EXPERIMENT_ENABLED=true
EXPERIMENT_NAME=planner-prompt-apr-2026
EXPERIMENT_TYPE=prompt
EXPERIMENT_VARIANT_A_PLANNER_PROMPT_FILE=prompts/experiments/planner-variant-a.txt
EXPERIMENT_VARIANT_B_PLANNER_PROMPT_FILE=prompts/experiments/planner-variant-b.txt
```

Prompt experiments target the planner only. Prompt file paths are resolved relative to `backend/`.

## API and development

| Endpoint           | Method | Purpose                                             |
| ------------------ | ------ | --------------------------------------------------- |
| `/`                | `GET`  | Health check                                        |
| `/workflow`        | `POST` | Full synchronous workflow                           |
| `/workflow/stream` | `GET`  | Live SSE workflow stream                            |
| `/runs`            | `GET`  | Paginated run history                               |
| `/runs/{run_id}`   | `GET`  | Full run detail                                     |
| `/analytics/*`     | `GET`  | Summary, timeseries, tool, and experiment analytics |

The SSE stream emits `status`, `experiment_assigned`, `attempt_start`, `plan`, `step_start`, `step_done`, `attempt_complete`, and `final`. The `final` event returns the full `WorkflowRunEnvelope`.

Development commands:

```bash
cd backend && source .venv/bin/activate && pytest tests
cd frontend/ai-workflow-agent-platform-frontend && npm run build && npm run lint
```

Quick health check:

```bash
curl http://localhost:8000/
```

## Troubleshooting

- Frontend cannot connect: verify `VITE_API_URL`, backend availability, and CORS settings.
- Migrations fail: confirm PostgreSQL is running and `DATABASE_URL` points to an existing database.
- Web search is unavailable: set `TAVILY_API_KEY` in `backend/.env`.
