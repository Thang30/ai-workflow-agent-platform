from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.executor_agent import ExecutorAgent
from app.agents.planner_agent import PlannerAgent
from app.core.orchestrator import WorkflowOrchestrator

from sse_starlette.sse import EventSourceResponse

app = FastAPI()

allowed_origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
