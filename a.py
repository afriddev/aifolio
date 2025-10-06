ChatCompletionChunk(id='85503232ff244da3b0514823a56e5594', choices=[Choice(delta=ChoiceDelta(content='.', function_call=None, refusal=None, role=None, tool_calls=None, reasoning_content=None), finish_reason=None, index=0, logprobs=None, matched_stop=None)], created=1759767191, model='qwen/qwen3-next-80b-a3b-instruct', object='chat.completion.chunk', service_tier=None, system_fingerprint=None, usage=None)

ChatCompletionChunk(id='85503232ff244da3b0514823a56e5594', choices=[Choice(delta=ChoiceDelta(content=None, function_call=None, refusal=None, role=None, tool_calls=None, reasoning_content=None), finish_reason='stop', index=0, logprobs=None, matched_stop=151645)], created=1759767192, model='qwen/qwen3-next-80b-a3b-instruct', object='chat.completion.chunk', service_tier=None, system_fingerprint=None, usage=None)


ChatCompletionChunk(id='85503232ff244da3b0514823a56e5594', choices=[], created=1759767192, model='qwen/qwen3-next-80b-a3b-instruct', object='chat.completion.chunk', service_tier=None, system_fingerprint=None, usage=CompletionUsage(completion_tokens=50, prompt_tokens=903, total_tokens=953, completion_tokens_details=None, prompt_tokens_details=None, reasoning_tokens=0))




//




ChatCompletionChunk(id='685975367c694637803f6cef225b8ad6', choices=[Choice(delta=ChoiceDelta(content='😊', function_call=None, refusal=None, role=None, tool_calls=None, reasoning_content=None), finish_reason=None, index=0, logprobs=None, matched_stop=None)], created=1759767232, model='qwen/qwen3-next-80b-a3b-instruct', object='chat.completion.chunk', service_tier=None, system_fingerprint=None, usage=None)
ChatCompletionChunk(id='685975367c694637803f6cef225b8ad6', choices=[Choice(delta=ChoiceDelta(content=None, function_call=None, refusal=None, role=None, tool_calls=None, reasoning_content=None), finish_reason='stop', index=0, logprobs=None, matched_stop=151645)], created=1759767232, model='qwen/qwen3-next-80b-a3b-instruct', object='chat.completion.chunk', service_tier=None, system_fingerprint=None, usage=None)
ChatCompletionChunk(id='685975367c694637803f6cef225b8ad6', choices=[], created=1759767232, model='qwen/qwen3-next-80b-a3b-instruct', object='chat.completion.chunk', service_tier=None, system_fingerprint=None, usage=CompletionUsage(completion_tokens=192, prompt_tokens=966, total_tokens=1158, completion_tokens_details=None, prompt_tokens_details=None, reasoning_tokens=0))


# from openai import OpenAI
# import json
# from utils import GetNvidiaAPIKey

# client = OpenAI(
#   base_url="https://integrate.api.nvidia.com/v1",
#   api_key=GetNvidiaAPIKey()
# )

# completion = client.chat.completions.create(
#   model="openai/gpt-oss-120b",
#   messages=[{"role":"user","content":"Hey buddy how are you man "*30000}],
#   temperature=0.6,
#   top_p=0.7,
#   max_tokens=8000,
#   stream=False
# )

# print(completion)
