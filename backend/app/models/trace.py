from typing import List, Dict, Any, Optional


class StepTrace:
    def __init__(
        self,
        step: int,
        description: str,
        input: str,
        output: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ):
        self.step = step
        self.description = description
        self.input = input
        self.output = output
        self.tools = tools or []

    def to_dict(self):
        return {
            "step": self.step,
            "description": self.description,
            "input": self.input,
            "output": self.output,
            "tools": self.tools,
        }


class WorkflowRun:
    def __init__(
        self,
        query: str,
        final_answer: str,
        evaluation_score: int,
        evaluation_reason: str,
    ):
        self.query = query
        self.final_answer = final_answer
        self.evaluation_score = evaluation_score
        self.evaluation_reason = evaluation_reason

    def to_dict(self):
        return {
            "query": self.query,
            "final_answer": self.final_answer,
            "evaluation_score": self.evaluation_score,
            "evaluation_reason": self.evaluation_reason,
        }
