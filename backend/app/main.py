from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.agents.executor_agent import ExecutorAgent
from app.agents.planner_agent import PlannerAgent
from app.core.config import settings
from app.core.orchestrator import WorkflowOrchestrator

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

agent = ExecutorAgent()
planner = PlannerAgent()
orchestrator = WorkflowOrchestrator()


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/chat")
def chat(input: dict):
    query = input.get("query", "")
    response = agent.run(query)
    print("LLM response:", response)
    return {"response": response}


@app.post("/plan")
def plan(input: dict):
    query = input.get("query", "")
    steps = planner.run(query)
    print("Generated plan:", steps)
    return {"plan": steps}


@app.post("/workflow")
def workflow(input: dict):
    query = input.get("query", "")
    result = orchestrator.run(query)
    print("Workflow result:", result)
    return result


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


@app.get("/runs/{run_id}")
def workflow_run(run_id: UUID):
    result = orchestrator.get_run(str(run_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    return result
