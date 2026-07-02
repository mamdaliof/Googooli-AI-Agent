import logging
from src.agent import OpenClawAgent

class SignalConnector:
    def __init__(self, agent: OpenClawAgent):
        self.agent = agent

    def run(self):
        # Stub for signal-cli D-Bus or REST API connection
        logging.info("Starting Signal Connector stub...")
