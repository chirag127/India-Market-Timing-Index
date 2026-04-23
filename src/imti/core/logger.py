"""Structured logging for the IMTI system."""

import logging
import sys
from datetime import datetime


class IMTIFormatter(logging.Formatter):
    """Custom log formatter with timestamp, level, and module."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        module = record.module
        level = record.levelname
        msg = record.getMessage()
        return f"{timestamp} [{level:>7}] {module:>20} | {msg}"


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Get a configured logger for the given module name."""
    logger = logging.getLogger(f"imti.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(IMTIFormatter())
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
