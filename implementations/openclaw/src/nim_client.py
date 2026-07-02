import json
import logging
import requests
import time
from typing import Dict, Any, List, Optional

class NIMClient:
    def __init__(self, api_key: str, base_url: str = "https://integrate.api.nvidia.com/v1", model_name: str = "meta/llama-3.1-70b-instruct"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = 15.0

    def chat_completion(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None, temperature: float = 0.7, max_tokens: int = 1024) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if tools:
            payload["tools"] = tools



        max_attempts = 3
        backoff = 1.0
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]
            except Exception as e:
                logging.warning(f"Nvidia NIM API Attempt {attempt} failed: {e}")
                if attempt == max_attempts:
                    logging.error(f"Nvidia NIM API Error: {e}")
                    raise e
                time.sleep(backoff)
                backoff *= 2.0

