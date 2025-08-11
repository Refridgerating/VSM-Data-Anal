from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path.home() / ".vsm-gui"
LOG_FILE = LOG_DIR / "vsm.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("vsm_gui")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

__all__ = ["logger", "LOG_FILE"]
