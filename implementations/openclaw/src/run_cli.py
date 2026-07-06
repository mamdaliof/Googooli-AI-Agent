import os
import sys
import argparse
from src.config import Config
from src.agent import OpenClawAgent

def main():
    parser = argparse.ArgumentParser(description="Googooli OpenClaw CLI Agent")
    parser.add_argument("--prompt", type=str, help="Prompt to run non-interactively")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    env_path = os.path.join(project_dir, ".env")
    config = Config(env_path)
    if not config.nvidia_api_key:
        print("Error: NVIDIA_API_KEY missing in .env")
        sys.exit(1)
        
    agent = OpenClawAgent(config)

    if args.prompt:
        try:
            reply = agent.handle_message(args.prompt)
            print(reply)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    print("Googooli OpenClaw CLI Agent (type 'exit' to quit)")
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.strip().lower() == "exit":
                break
            reply = agent.handle_message(user_input)
            print(f"Googooli: {reply}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()

