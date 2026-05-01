import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.xiaomimimo.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "your-api-key-here")
    llm_model: str = os.getenv("LLM_MODEL", "mimo-v2.5-pro")
    max_context_tokens: int = 100_000
    agent_max_tokens: int = 16_384
    memory_backend: str = "redis"  # "redis" or "inmemory"
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ws_host: str = "0.0.0.0"
    ws_port: int = 8765
    api_host: str = "0.0.0.0"
    api_port: int = 8000


default_config = Config()
