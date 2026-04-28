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
