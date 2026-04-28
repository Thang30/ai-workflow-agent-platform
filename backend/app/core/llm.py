from huggingface_hub import InferenceClient
from .config import settings 


class LLMClient:
    def __init__(self):
        print("The model is:", settings.model)
        self.client = InferenceClient(api_key=settings.hf_token)
        self.model = settings.model

    def chat(self, message: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": message}
            ],
        )

        return response.choices[0].message.content