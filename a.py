from openai import OpenAI
import json
from utils import GetNvidiaAPIKey

client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=GetNvidiaAPIKey()
)

completion = client.chat.completions.create(
  model="bytedance/seed-oss-36b-instruct",
  messages=[{"role":"user","content":"Which number is larger, 9.11 or 9.8?"*20000}],
  temperature=0.6,
  top_p=0.7,
  max_tokens=8000,
  stream=False
)

print(completion)
