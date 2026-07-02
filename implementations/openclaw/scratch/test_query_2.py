import os
import sys
import requests
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

payload = {
    "model": model_name,
    "messages": [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS + "\n\nCRITICAL: Do NOT generate a tool call or function call named 'ACTION_SEND_FILE'. ACTION_SEND_FILE is NOT a function tool; it is a text tag that you must print in your final message content (plain text) after all tool executions are complete. If you need to download a paper or file, and you do not know the exact URL, you MUST search the web first using 'google_web_search' to locate the correct URL. Do NOT hallucinate mock URLs (like example.com) for download_file."},
        {"role": "user", "content": "Search the web for a CVPR 2024 paper about YOLO, get its actual PDF download URL (which must end in .pdf), and download it to /tmp/cvpr_paper.pdf."}
    ],
    "tools": TOOLS_SCHEMA,
    "temperature": 0.7,
    "max_tokens": 1024
}

print("Sending request to NIM API...")
try:
    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=15.0
    )
    print("Status Code:", response.status_code)
    print("Response text:", response.text)
except Exception as e:
    print("Request exception:", e)
