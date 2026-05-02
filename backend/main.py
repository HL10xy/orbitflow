from __future__ import annotations

import uvicorn
from config import default_config as cfg


def main():
    uvicorn.run(
        "api.routes:app",
        host=cfg.api_host,
        port=cfg.api_port,
        reload=cfg.debug,
    )


if __name__ == "__main__":
    main()
