"""Configuration package public API."""

import sys

from app.config import config as config
from app.utils.logging_utils import configure_terminal_logger


def _init_logger() -> None:
    """Configure the process logger once when the config package is imported."""
    configure_terminal_logger(
        sys.stdout,
        level=getattr(config, "log_level", "INFO"),
        colorize=False,
    )


_init_logger()

__all__ = ["config"]
