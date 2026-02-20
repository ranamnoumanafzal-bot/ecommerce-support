import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://router.huggingface.co/v1/",
    api_key=os.getenv("HUGGINGFACE_API_KEY")
)

try:
    print("Testing Hugging Face API connection...")
    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=[{"role": "user", "content": "Hello, are you working?"}],
        max_tokens=10
    )
    print("API Success!")
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("API FAILED!")
    print("Error:", str(e))
