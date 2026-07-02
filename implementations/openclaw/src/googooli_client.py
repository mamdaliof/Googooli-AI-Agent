import logging
import requests
from typing import Dict, Any, Optional

class GoogooliClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/") if api_url else ""
        self.api_key = api_key
        self.timeout = 3.0

    def query_context(self, query: str) -> Optional[str]:
        """Fetch relevant note context from the main Googooli instance."""
        if not self.api_url:
            logging.warning("Googooli API URL not configured. Skipping context query.")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        params = {"q": query}
        try:
            response = requests.get(
                f"{self.api_url}/context",
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("context", "")
        except Exception as e:
            logging.warning(f"Failed to query Googooli context: {e}")
            return None
