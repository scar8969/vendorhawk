"""
Structured Logging Configuration

Provides structured logging using structlog for better observability
and debugging across the application.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.config import settings


def setup_logging() -> None:
    """
    Configure structured logging for the application

    Sets up both structlog for structured logging and standard logging
    for compatibility with third-party libraries.
    """
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.is_development and settings.ENABLE_DEBUG_LOGGING:
        # Development: Console-friendly output with colors
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # Production: JSON output for log aggregation
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging for third-party libraries
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.ENABLE_DEBUG_LOGGING else logging.INFO,
    )

    # Set lower log level for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance

    Args:
        name: Logger name (usually __name__ from calling module)

    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)


# Initialize logging on module import
setup_logging()

# Export logger
logger = get_logger(__name__)
