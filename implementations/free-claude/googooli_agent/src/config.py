import os

class Config:
    def __init__(self, env_path: str = ".env"):
        self.env_data = {}
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        self.env_data[k.strip()] = v.strip()

    def get(self, key: str, default: str = "") -> str:
        return os.environ.get(key, self.env_data.get(key, default))

    @property
    def nvidia_api_key(self) -> str:
        return self.get("NVIDIA_API_KEY")

    @property
    def nvidia_model_name(self) -> str:
        return self.get("NVIDIA_MODEL_NAME", "meta/llama-3.1-70b-instruct")

    @property
    def nvidia_api_base(self) -> str:
        return self.get("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")

    @property
    def googooli_api_url(self) -> str:
        return self.get("GOOGOOLI_API_URL")

    @property
    def googooli_api_key(self) -> str:
        return self.get("GOOGOOLI_API_KEY")

    @property
    def telegram_bot_token(self) -> str:
        return self.get("TELEGRAM_BOT_TOKEN")

    @property
    def slack_bot_token(self) -> str:
        return self.get("SLACK_BOT_TOKEN")

    @property
    def tavily_api_key(self) -> str:
        return self.get("TAVILY_API_KEY")
