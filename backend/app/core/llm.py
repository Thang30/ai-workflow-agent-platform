from huggingface_hub import InferenceClient
from .config import settings


class LLMClient:
    def __init__(self, model: str | None = None):
        self.client = InferenceClient(api_key=settings.hf_token)
        self.model = model or settings.model

    def chat(self, message: str, model: str | None = None) -> str:
        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=[{"role": "user", "content": message}],
        )

        return response.choices[0].message.content
