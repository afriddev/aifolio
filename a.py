from openai import OpenAI
import json
from utils import GetNvidiaAPIKey

client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=GetNvidiaAPIKey()
)

completion = client.chat.completions.create(
  model="openai/gpt-oss-120b",
  messages=[{"role":"user","content":"Hey buddy how are you man "*30000}],
  temperature=0.6,
  top_p=0.7,
  max_tokens=8000,
  stream=False
)

print(completion)
