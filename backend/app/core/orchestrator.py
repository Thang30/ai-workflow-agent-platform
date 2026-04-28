from app.agents.planner_agent import PlannerAgent
from app.agents.executor_agent import ExecutorAgent


class WorkflowOrchestrator:
    def __init__(self):
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()

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

        for step in plan:
            step_desc = step["description"]
            enriched_input = f"""
            Context so far:
            {context}

            Current step:
            {step_desc}
            """

            result = self.executor.run(enriched_input)

            context += f"\nStep {step['step']}: {result}\n"

            results.append(
                {"step": step["step"], "description": step_desc, "result": result}
            )

        return {"input": query, "plan": plan, "results": results}
