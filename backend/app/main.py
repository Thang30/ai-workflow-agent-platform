from fastapi import FastAPI
from app.agents.executor_agent import ExecutorAgent
from app.agents.planner_agent import PlannerAgent

app = FastAPI()

agent = ExecutorAgent()
planner = PlannerAgent()


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
    return {"plan": steps}