import os
import sys
import time
import subprocess
from dotenv import load_dotenv

sys.path.append("/home/farhad/openclaw")
load_dotenv("/home/farhad/openclaw/.env")

from src.config import Config
from src.agent import OpenClawAgent

def run_openclaw(prompt: str):
    config = Config("/home/farhad/openclaw/.env")
    agent = OpenClawAgent(config)
    
    print(f"\n--- OpenClaw Agent Query: '{prompt}' ---")
    start_time = time.time()
    try:
        reply = agent.handle_message(prompt)
        elapsed = time.time() - start_time
        print(f"Elapsed Time: {elapsed:.2f}s")
        print("Final Reply:")
        print(reply)
    except Exception as e:
        print(f"Error running OpenClaw: {e}")

def run_googooli_agy(prompt: str):
    print(f"\n--- Googooli (agy) Query: '{prompt}' ---")
    start_time = time.time()
    try:
        cmd = ["agy", "--dangerously-skip-permissions", "--print", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90.0)
        elapsed = time.time() - start_time
        print(f"Elapsed Time: {elapsed:.2f}s")
        print(f"Exit Code: {result.returncode}")
        print("Stdout:")
        print(result.stdout)
        if result.stderr:
            print("Stderr:")
            print(result.stderr)
    except Exception as e:
        print(f"Error running agy: {e}")

if __name__ == "__main__":
    prompts = [
        "Find the Github repository URL for context7 package on npm, and tell me the name of the main repository.",
        "Search the web for CVPR 2026 dates and location, fetch the main page to confirm, and tell me."
    ]
    
    for i, p in enumerate(prompts):
        print(f"\n=======================================================")
        print(f"TEST CASE {i+1}")
        print(f"=======================================================")
        run_openclaw(p)
        run_googooli_agy(p)
