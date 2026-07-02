import os
import sys
import requests
import json
from dotenv import load_dotenv
sys.path.append("/home/farhad/openclaw")

from src.tools import TOOLS_SCHEMA
from src.persona import SYSTEM_INSTRUCTIONS

load_dotenv("/home/farhad/openclaw/.env")

api_key = os.getenv("NVIDIA_API_KEY")
base_url = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1").rstrip("/")
model_name = os.getenv("NVIDIA_MODEL_NAME", "meta/llama-3.1-8b-instruct")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# The messages list exactly as sent in the failing task-893, but with sanitization!
messages_sanitized = [
  {
    "role": "system",
    "content": SYSTEM_INSTRUCTIONS
  },
  {
    "role": "user",
    "content": "Search the web for CVPR 2026 dates and location, fetch the main page to confirm, and tell me."
  },
  {
    "role": "assistant",
    "content": ";;",
    "tool_calls": [
      {
        "id": "call-2e8769cd-ce7f-414e-84d2-308ec9705e9c",
        "type": "function",
        "function": {
          "name": "google_web_search",
          "arguments": "{\"query\":\"CVPR 2026 dates and location\"}"
        }
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call-2e8769cd-ce7f-414e-84d2-308ec9705e9c",
    "name": "google_web_search",
    "content": "Result #1:\nTitle: 2026 Dates and Deadlines..."
  }
]

payload = {
    "model": model_name,
    "messages": messages_sanitized,
    "tools": TOOLS_SCHEMA,
    "temperature": 0.7,
    "max_tokens": 1024
}

print("Sending sanitized request to NIM API...")
response = requests.post(
    f"{base_url}/chat/completions",
    headers=headers,
    json=payload,
    timeout=15.0
)
print("Status Code:", response.status_code)
print("Response text:", response.text)
