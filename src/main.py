from pathlib import Path

import uvicorn

from . import xbot


def main():
    uvicorn.run(
        f"{Path(__file__).parent.name}:app",
        host=xbot.config.host,
        port=xbot.config.port,
        log_level="info",
        reload=True,
    )
