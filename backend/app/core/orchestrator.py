import json
from datetime import datetime

from app.agents.planner_agent import PlannerAgent
from app.agents.executor_agent import ExecutorAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.models.trace import StepTrace


def save_trace(data):
    filename = f"trace_{datetime.now().timestamp()}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


class WorkflowOrchestrator:
    def __init__(self):
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.reviewer = ReviewerAgent()

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
            step_desc = step["description"]
            enriched_input = f"""
            Context so far:
            {context}

            Current step:
            {step_desc}
            """

            result = self.executor.run(enriched_input)

            traces.append(
                StepTrace(
                    step=step["step"],
                    description=step_desc,
                    input=enriched_input,
                    output=result,
                ).to_dict()
            )

            context += f"\nStep {step['step']}: {result}\n"

            results.append(
                {"step": step["step"], "description": step_desc, "result": result}
            )

        formatted_results = "\n".join(
            [f"Step {r['step']}: {r['result']}" for r in results]
        )

        final_answer = self.reviewer.run(query, plan, formatted_results)

        save_trace(
            {"input": query, "plan": plan, "traces": traces, "final": final_answer}
        )

        return {"input": query, "plan": plan, "traces": traces, "final": final_answer}
