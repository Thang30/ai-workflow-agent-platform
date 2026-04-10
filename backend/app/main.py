from fastapi import FastAPI
from app.agents.executor_agent import ExecutorAgent

app = FastAPI()

agent = ExecutorAgent()


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/chat")
def chat(input: dict):
    query = input.get("query", "")
    response = agent.run(query)
    return {"response": response}