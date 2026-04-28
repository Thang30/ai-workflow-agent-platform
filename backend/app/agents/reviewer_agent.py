from app.core.llm import LLMClient


class ReviewerAgent:
    def __init__(self):
        self.llm = LLMClient()

    def run(self, query: str, steps: list, results: list) -> str:
        """
        Reviews and synthesizes all step results into a final answer.
        """

        prompt = f"""
You are a senior AI reviewer.

Your job:
- Combine all step results into a clear, structured final answer
- Remove redundancy
- Fix inconsistencies
- Improve clarity and quality

User request:
{query}

Steps:
{steps}

Results:
{results}

Output:
- Clear final answer
- Well-structured
- Concise but complete
"""

        return self.llm.chat(prompt)
