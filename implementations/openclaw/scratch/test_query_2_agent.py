import os
import sys
from dotenv import load_dotenv
sys.path.append("/home/farhad/openclaw")

from src.config import Config
from src.agent import OpenClawAgent

load_dotenv("/home/farhad/openclaw/.env")

config = Config("/home/farhad/openclaw/.env")
agent = OpenClawAgent(config)

prompt = "Search the web for CVPR 2026 dates and location, fetch the main page to confirm, and tell me."

print("Running agent...")
try:
    reply = agent.handle_message(prompt)
    print("Agent reply:")
    print(reply)
except Exception as e:
    print("Agent error:", e)
