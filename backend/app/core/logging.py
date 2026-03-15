"""
Logging configuration using Loguru.
"""

import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """Configure Loguru with console + rotating file sinks."""

    # Remove default sink
    logger.remove()

    # ── Console sink ────────────────────────────────────────────
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # ── File sink (rotating) ───────────────────────────────────
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_path),
        level=settings.log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} — {message}"
        ),
    )

    logger.info("Logging initialised  (level={})", settings.log_level)
