from app.core.llm import LLMClient


class ReviewerAgent:
    def __init__(self):
        self.llm = LLMClient()

    def run(
        self,
        query: str,
        steps: list,
        results: list,
        improvement_hint: str | None = None,
    ) -> str:
        """
        Reviews and synthesizes all step results into a final answer.
        """

        improvement_section = ""
        if improvement_hint:
            improvement_section = f"""
Retry guidance from the previous attempt:
{improvement_hint}

Address these issues directly in the final answer.
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

{improvement_section}

Output:
- Clear final answer
- Well-structured
- Concise but complete
"""

        return self.llm.chat(prompt)
