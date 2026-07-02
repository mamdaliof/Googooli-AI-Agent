import os
import sys
import logging
from src.config import Config
from src.agent import OpenClawAgent
from src.channels.telegram_conn import TelegramConnector

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    env_path = os.path.join(project_dir, ".env")
    config = Config(env_path)
    if not config.telegram_bot_token:
        print("Error: TELEGRAM_BOT_TOKEN missing in .env")
        sys.exit(1)

    agent = OpenClawAgent(config)
    connector = TelegramConnector(config.telegram_bot_token, agent)
    connector.run()

if __name__ == "__main__":
    main()

