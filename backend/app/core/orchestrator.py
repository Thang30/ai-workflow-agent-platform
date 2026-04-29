import asyncio
import json
from datetime import datetime

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.executor_agent import ExecutorAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.models.trace import StepTrace, WorkflowRun


def save_trace(data):
    filename = f"trace_{datetime.now().timestamp()}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


class WorkflowOrchestrator:
    def __init__(self):
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.reviewer = ReviewerAgent()
        self.evaluator = EvaluationAgent()

    def _stream_event(self, event: str, data):
        return {"event": event, "data": json.dumps(data, ensure_ascii=False)}

    def _execute_step(self, step: dict, context: str):
        step_desc = step["description"]
        enriched_input = f"""
            Context so far:
            {context}

            Current step:
            {step_desc}
            """

        execution = self.executor.execute(enriched_input)
        result = execution["output"]
        tools = execution["tools"]

        trace = StepTrace(
            step=step["step"],
            description=step_desc,
            input=enriched_input,
            output=result,
            tools=tools,
        ).to_dict()

        next_context = f"{context}\nStep {step['step']}: {result}\n"
        result_entry = {
            "step": step["step"],
            "description": step_desc,
            "result": result,
            "tools": tools,
        }

        return result_entry, trace, next_context

    def _review_workflow(
        self,
        query: str,
        plan: list,
        results: list,
    ) -> str:
        formatted_results = "\n".join(
            [f"Step {result['step']}: {result['result']}" for result in results]
        )

        return self.reviewer.run(query, plan, formatted_results)

    def _evaluate_workflow(self, query: str, final_answer: str) -> WorkflowRun:
        evaluation = self.evaluator.run(query, final_answer)

        return WorkflowRun(
            query=query,
            final_answer=final_answer,
            evaluation_score=evaluation["score"],
            evaluation_reason=evaluation["reasoning"],
        )

    def _save_workflow_run(
        self,
        query: str,
        plan: list,
        traces: list,
        workflow_run: WorkflowRun,
    ):
        save_trace(
            {
                "input": query,
                "plan": plan,
                "traces": traces,
                "final": workflow_run.final_answer,
                "workflow_run": workflow_run.to_dict(),
            }
        )

    def run(self, query: str):
        """
        Full workflow:
        1. Generate plan
        2. Execute each step
        3. Collect results
        """

        plan = self.planner.run(query)

        results = []
        context = ""
        traces = []

        for step in plan:
            result_entry, trace, context = self._execute_step(step, context)
            traces.append(trace)
            results.append(result_entry)

        final_answer = self._review_workflow(query, plan, results)
        workflow_run = self._evaluate_workflow(query, final_answer)
        self._save_workflow_run(query, plan, traces, workflow_run)

        return {
            "input": query,
            "plan": plan,
            "traces": traces,
            "final": workflow_run.final_answer,
            "workflow_run": workflow_run.to_dict(),
        }

    async def stream_events(self, query: str):
        yield self._stream_event("status", "🧠 Planning...")

        plan = self.planner.run(query)
        yield self._stream_event("plan", plan)
        yield self._stream_event("status", "⚙️ Executing...")

        results = []
        traces = []
        context = ""

        for step in plan:
            yield self._stream_event(
                "step_start",
                {"step": step["step"], "description": step["description"]},
            )

            result_entry, trace, context = self._execute_step(step, context)
            traces.append(trace)
            results.append(result_entry)

            yield self._stream_event(
                "step_done",
                {
                    "step": step["step"],
                    "output": result_entry["result"],
                    "tools": result_entry["tools"],
                },
            )

            await asyncio.sleep(0.1)

        yield self._stream_event("status", "🔍 Reviewing...")

        final_answer = self._review_workflow(query, plan, results)

        yield self._stream_event("status", "📏 Evaluating...")

        workflow_run = self._evaluate_workflow(query, final_answer)
        self._save_workflow_run(query, plan, traces, workflow_run)

        yield self._stream_event("final", workflow_run.to_dict())
