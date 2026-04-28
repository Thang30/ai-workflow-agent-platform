from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.executor_agent import ExecutorAgent
from app.agents.planner_agent import PlannerAgent
from app.core.orchestrator import WorkflowOrchestrator

from sse_starlette.sse import EventSourceResponse
import asyncio

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


def build_workflow_stream(query: str):
    async def event_generator():
        yield {"event": "status", "data": "🧠 Planning..."}

        plan = orchestrator.planner.run(query)
        yield {"event": "plan", "data": plan}

        context = ""

        for step in plan:
            step_desc = step["description"]

            yield {
                "event": "step_start",
                "data": {"step": step["step"], "description": step_desc},
            }

            enriched_input = f"""
Context:
{context}

Step:
{step_desc}
"""

            result = orchestrator.executor.run(enriched_input)

            context += f"\nStep {step['step']}: {result}\n"

            yield {
                "event": "step_done",
                "data": {"step": step["step"], "output": result},
            }

            await asyncio.sleep(0.1)  # small delay for UX

        yield {"event": "status", "data": "🧠 Reviewing..."}

        final = orchestrator.reviewer.run(query, plan, [])

        yield {"event": "final", "data": final}

    return EventSourceResponse(event_generator())


@app.get("/workflow/stream")
async def workflow_stream(query: str):
    return build_workflow_stream(query)
