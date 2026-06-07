import openai
import os
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
api_base = os.getenv('OPENAI_API_BASE')
if api_base:
    openai.api_base = api_base
model = os.getenv('MODEL_NAME', 'gpt-3.5-turbo')
print(f'API Base: {openai.api_base}')
print(f'Model: {model}')
try:
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{'role':'user','content':'2+2=?'}],
        max_tokens=10,
        temperature=0
    )
    print('✅ 成功！回复:', response.choices[0].message.content)
except Exception as e:
    print('❌ 失败:', e)
