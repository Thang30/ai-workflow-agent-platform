from app.agents.planner_agent import PlannerAgent
from app.agents.executor_agent import ExecutorAgent
from app.agents.reviewer_agent import ReviewerAgent


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

        formatted_results = "\n".join(
            [f"Step {r['step']}: {r['result']}" for r in results]
        )

        final_answer = self.reviewer.run(query, plan, formatted_results)

        return {"input": query, "plan": plan, "results": results, "final": final_answer}
