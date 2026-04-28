from typing import List, Dict, Any


class StepTrace:
    def __init__(self, step: int, description: str, input: str, output: str):
        self.step = step
        self.description = description
        self.input = input
        self.output = output

    def to_dict(self):
        return {
            "step": self.step,
            "description": self.description,
            "input": self.input,
            "output": self.output
        }