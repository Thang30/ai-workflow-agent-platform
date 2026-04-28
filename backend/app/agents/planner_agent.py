import json
from app.core.llm import LLMClient


class PlannerAgent:
    def __init__(self):
        self.llm = LLMClient()

    def _clean_json(self, text: str) -> str:
        return text.strip().replace("```json", "").replace("```", "")

    def _extract_steps(self, text: str):
        cleaned_text = self._clean_json(text)
        decoder = json.JSONDecoder()

        for index, char in enumerate(cleaned_text):
            if char not in "[{":
                continue

            try:
                parsed, _ = decoder.raw_decode(cleaned_text[index:])
            except json.JSONDecodeError:
                continue

            if isinstance(parsed, list):
                return parsed

        raise ValueError("No valid JSON step list found in model response")

    def run(self, query: str):
        """
        Generates a step-by-step plan from user query.
        Returns a list of steps.
        """

        prompt = """
You are a planning agent.

Break the user's request into clear steps.

Rules:
- Output MUST be valid JSON
- Output MUST be a list of steps
- Each step must have:
- step (number)
- description (string)

Example:
[
  {"step": 1, "description": "Research the company"},
  {"step": 2, "description": "Summarize findings"}
]

User request:
""" + query + "\n"

        response = self.llm.chat(prompt)

        try:
            steps = self._extract_steps(response)
            return steps
        except Exception as e:
            print("Error parsing JSON:", e)
            print("LLM response was:", response)
            return [{"step": 1, "description": query}]
        
