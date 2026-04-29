from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.agents.executor_agent import ExecutorAgent
from app.agents.planner_agent import PlannerAgent
from app.core.config import settings
from app.core.orchestrator import WorkflowOrchestrator
from app.tools.registry import DEFAULT_TOOL_REGISTRY

from sse_starlette.sse import EventSourceResponse

app = FastAPI()

allowed_origins = [origin.rstrip("/") for origin in settings.frontend_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=settings.frontend_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = ExecutorAgent(tools=DEFAULT_TOOL_REGISTRY)
planner = PlannerAgent()
orchestrator = WorkflowOrchestrator()


def _get_query(payload: dict):
    return payload.get("query", "")


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/chat")
def chat(payload: dict):
    query = _get_query(payload)
    response = agent.run(query)
    return {"response": response}


@app.post("/plan")
def plan(payload: dict):
    query = _get_query(payload)
    steps = planner.run(query)
    return {"plan": steps}


@app.post("/workflow")
def workflow(payload: dict):
    return orchestrator.run(_get_query(payload))


@app.get("/workflow/stream")
async def workflow_stream(query: str):
    return EventSourceResponse(orchestrator.stream_events(query))


@app.get("/runs/stats")
def workflow_run_stats():
    return orchestrator.get_run_stats()


@app.get("/runs")
def workflow_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return orchestrator.list_runs(page=page, page_size=page_size)


@app.get("/analytics/summary")
def analytics_summary(days: int = Query(default=7, ge=1, le=90)):
    return orchestrator.get_analytics_summary(days=days)


@app.get("/analytics/timeseries")
def analytics_timeseries(days: int = Query(default=7, ge=1, le=90)):
    return orchestrator.get_analytics_timeseries(days=days)


@app.get("/analytics/distribution")
def analytics_distribution(days: int = Query(default=7, ge=1, le=90)):
    return orchestrator.get_analytics_distribution(days=days)


@app.get("/analytics/tools")
def analytics_tools(days: int = Query(default=7, ge=1, le=90)):
    return orchestrator.get_analytics_tools(days=days)


@app.get("/analytics/experiment-summary")
def analytics_experiment_summary(days: int = Query(default=7, ge=1, le=90)):
    return orchestrator.get_active_experiment_summary(days=days)


@app.get("/runs/{run_id}")
def workflow_run(run_id: UUID):
    result = orchestrator.get_run(str(run_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    return result
