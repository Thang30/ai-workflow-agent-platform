import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

client = InferenceClient(
    api_key=os.environ["HF_TOKEN"],
)

completion = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct:novita",
    messages=[
        {
            "role": "user",
            "content": "What is the capital of France?"
        }
    ],
)

print(completion.choices[0].message)