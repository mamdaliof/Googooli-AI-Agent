import requests
import os
import sys

TOKEN = os.getenv("GOOGOOLI_TELEGRAM_TOKEN")
CHAT_ID = os.getenv("GOOGOOLI_CHAT_ID")

if not TOKEN or not CHAT_ID:
    print("Environment variables missing. Reading from .env")
    env_path = ".googooli/config/.env"
    with open(env_path, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                val = val.replace('"', '').replace("'", "")
                if key == "GOOGOOLI_TELEGRAM_TOKEN": TOKEN = val
                if key == "GOOGOOLI_CHAT_ID": CHAT_ID = val

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
resp = requests.post(url, json={"chat_id": CHAT_ID, "text": "Testing API connection."})
print(resp.status_code)
print(resp.text)
