import os

import uvicorn
from loguru import logger

from app.config import config

if __name__ == "__main__":
    # Allow an env override so the same entry point works inside a container,
    # instead of freezing the loopback-only default that config.toml ships with.
    host = os.environ.get("MPT_LISTEN_HOST") or config.listen_host
    port = int(os.environ.get("MPT_LISTEN_PORT") or config.listen_port)
    log_level = (os.environ.get("MPT_LOG_LEVEL") or "warning").lower()

    if host in {"0.0.0.0", "::"}:
        logger.warning(
            "API is binding to all interfaces on port {}; make sure app.api_key is set "
            "before exposing it outside a trusted network.",
            port,
        )
    logger.info("start server, docs: http://127.0.0.1:{}/docs", port)
    # FFmpeg detection lives in app/services/task.py so the API, CLI and WebUI
    # share one pipeline; it is intentionally not repeated here.
    uvicorn.run(
        app="app.asgi:app",
        host=host,
        port=port,
        reload=config.reload_debug,
        log_level=log_level,
    )
