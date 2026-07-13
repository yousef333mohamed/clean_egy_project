"""Structured application logging."""

import logging
import sys

import structlog


def configure_logging(level: str = "INFO", environment: str = "development") -> None:
    """Configure human-readable local logs and structured production JSON."""
    logging.basicConfig(stream=sys.stdout, level=level.upper(), format="%(message)s", force=True)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer() if environment.casefold() in {"production", "staging"} else structlog.dev.ConsoleRenderer(colors=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level.upper())),
    )


def get_logger(name: str):
    """Return a structured logger."""
    return structlog.get_logger(name)
