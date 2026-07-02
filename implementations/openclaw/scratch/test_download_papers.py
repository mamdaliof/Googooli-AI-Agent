import os
import sys
import time
from dotenv import load_dotenv

sys.path.append("/home/farhad/openclaw")
load_dotenv("/home/farhad/openclaw/.env")

from src.config import Config
from src.agent import OpenClawAgent

def run_test(prompt: str):
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

if __name__ == "__main__":
    print("Testing arXiv paper download...")
    run_test("Find the arXiv paper '1706.03762' (Attention Is All You Need) and download its PDF to /tmp/arxiv_paper.pdf.")
    
    print("\nTesting CVPR paper download...")
    run_test("Search the web for the CVPR 2024 YOLO-World paper, locate its PDF URL on openaccess.thecvf.com, then download it using download_file to /tmp/cvpr_paper.pdf.")
