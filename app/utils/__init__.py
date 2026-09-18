"""Shared utility exports for the application."""

from loguru import logger

__all__ = ["logger"]


def __getattr__(name: str):
    """Provide a helpful error for unsupported utility package attributes."""
    raise AttributeError(f"module 'app.utils' has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(__all__))


# Keep the package export intentionally small. Utility modules should be imported
# explicitly (for example, ``from app.utils import utils``) to avoid eager imports.

