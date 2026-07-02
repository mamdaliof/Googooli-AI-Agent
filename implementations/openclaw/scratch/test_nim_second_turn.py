import os
import sys
from dotenv import load_dotenv
sys.path.append("/home/farhad/openclaw")

from src.nim_client import NIMClient
from src.tools import TOOLS_SCHEMA, google_web_search
from src.persona import SYSTEM_INSTRUCTIONS

load_dotenv("/home/farhad/openclaw/.env")

client = NIMClient(
    api_key=os.getenv("NVIDIA_API_KEY"),
    base_url=os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1"),
    model_name=os.getenv("NVIDIA_MODEL_NAME", "meta/llama-3.1-8b-instruct")
)

messages = [
    {"role": "system", "content": SYSTEM_INSTRUCTIONS},
    {"role": "user", "content": "hi"}
]

print("First turn:")
res1 = client.chat_completion(messages, tools=TOOLS_SCHEMA)
print(res1)

if res1.get("tool_calls"):
    messages.append(res1)
    for tool_call in res1["tool_calls"]:
        func_name = tool_call["function"]["name"]
        print(f"Calling tool: {func_name}")
        # Execute tool
        if func_name == "google_web_search":
            result = google_web_search("hi")
        else:
            result = "mocked"
        
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "name": func_name,
            "content": result
        })
    
    print("Second turn:")
    res2 = client.chat_completion(messages, tools=TOOLS_SCHEMA)
    print(res2)
