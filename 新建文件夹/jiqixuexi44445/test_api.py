@"
import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")
if api_base:
    openai.api_base = api_base

model = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

print(f"Using API base: {openai.api_base}")
print(f"Using model: {model}")

try:
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    print("API call successful:", response.choices[0].message.content)
except Exception as e:
    print("API call failed:", e)
"@ | Out-File -Encoding utf8 test_api.py