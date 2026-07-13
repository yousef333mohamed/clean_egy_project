"""Structured application logging."""

import logging
import sys

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Configure JSON logs suitable for local and container execution."""
    logging.basicConfig(stream=sys.stdout, level=level.upper(), format="%(message)s", force=True)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level.upper())),
    )


def get_logger(name: str):
    """Return a structured logger."""
    return structlog.get_logger(name)
