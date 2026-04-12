"""
Logging configuration using loguru.
Handles Windows console encoding (cp1252) by reconfiguring streams to utf-8.
"""

import sys
import os
from loguru import logger

# Remove default handler
logger.remove()

# Force utf-8 on Windows console BEFORE adding loguru handlers
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Console handler with color
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
    level="DEBUG",
)

# File handler for production (file sinks do support encoding)
logger.add(
    "logs/krishimitra_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    encoding="utf-8",
)

__all__ = ["logger"]
