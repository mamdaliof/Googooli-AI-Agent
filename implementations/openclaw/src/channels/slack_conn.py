import logging
from typing import Optional
from src.agent import OpenClawAgent

class SlackConnector:
    def __init__(self, token: str, agent: OpenClawAgent):
        self.token = token
        self.agent = agent

    def handle_slack_event(self, event_data: dict) -> Optional[str]:
        event = event_data.get("event", {})
        if event.get("type") == "message" and not event.get("bot_id"):
            text = event.get("text", "")
            user = event.get("user", "")
            reply = self.agent.handle_message(text, user_id=user)
            return reply
        return None

    def run(self):
        logging.info("Starting Slack Event Connector stub...")
