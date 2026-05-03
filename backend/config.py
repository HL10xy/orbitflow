import os
import sys
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.xiaomimimo.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "mimo-v2.5-pro")
    max_context_tokens: int = 100_000
    agent_max_tokens: int = 16_384
    api_host: str = os.getenv("ORBITFLOW_HOST", "127.0.0.1")
    api_port: int = 8000
    debug: bool = os.getenv("ORBITFLOW_DEBUG", "false").lower() in ("true", "1", "yes")
    api_key: str = os.getenv("ORBITFLOW_API_KEY", "")
    cors_origins: list[str] = None
    ws_rate_limit: int = 10  # max messages per second per connection

    def __post_init__(self):
        if self.cors_origins is None:
            origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000")
            self.cors_origins = [o.strip() for o in origins_str.split(",") if o.strip()]
        if not self.llm_api_key:
            print(
                "WARNING: LLM_API_KEY is not set. "
                "Set the LLM_API_KEY environment variable before starting.",
                file=sys.stderr,
            )


default_config = Config()
