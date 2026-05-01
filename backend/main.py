from __future__ import annotations

import uvicorn
from api.routes import app
from config import default_config as cfg


def main():
    uvicorn.run(
        "api.routes:app",
        host=cfg.api_host,
        port=cfg.api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
