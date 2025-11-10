"""Centralized logging configuration for PyPoE.

This module provides structured logging using Python's standard logging library
with enhanced formatting and context support.

Example:
    >>> from PyPoE.shared.logging import get_logger, configure_logging
    >>>
    >>> # Configure logging once at application startup
    >>> configure_logging(log_level="INFO")
    >>>
    >>> # Get logger instance in your modules
    >>> logger = get_logger(__name__)
    >>> logger.info("Loading file", filename="test.dat", size=1024)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Custom formatter that adds structured logging capabilities."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data.

        Args:
            record: The log record to format

        Returns:
            Formatted log message string
        """
        # Start with basic format
        base_msg = super().format(record)

        # Add structured data if present
        if hasattr(record, "structured_data") and record.structured_data:
            data_parts = [f"{k}={v}" for k, v in record.structured_data.items()]
            structured = " ".join(data_parts)
            return f"{base_msg} | {structured}"

        return base_msg


def configure_logging(
    log_level: str = "INFO",
    log_file: Path | None = None,
    format_string: str | None = None,
) -> None:
    """Configure structured logging for PyPoE.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file to write logs to
        format_string: Custom format string (default: includes timestamp and level)

    Example:
        >>> configure_logging(log_level="DEBUG", log_file=Path("pypoe.log"))
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create formatter
    formatter = StructuredFormatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # Configure root logger
    root_logger = logging.getLogger("PyPoE")
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.LoggerAdapter:
    """Get a logger instance with structured logging support.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger adapter that supports structured logging

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing file", filename="test.dat", records=100)
    """
    base_logger = logging.getLogger(name)

    class StructuredLoggerAdapter(logging.LoggerAdapter):
        """Logger adapter that adds structured data to log records."""

        def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
            """Process log call to extract structured data.

            Args:
                msg: Log message
                kwargs: Keyword arguments

            Returns:
                Tuple of (message, modified kwargs)
            """
            # Extract structured data from kwargs
            extra = kwargs.get("extra", {})
            structured_data = {}

            # Move non-logging kwargs to structured_data
            keys_to_remove = []
            for key, value in kwargs.items():
                if key not in ["exc_info", "stack_info", "stacklevel", "extra"]:
                    structured_data[key] = value
                    keys_to_remove.append(key)

            # Remove structured data from kwargs
            for key in keys_to_remove:
                kwargs.pop(key)

            # Add structured data to extra
            if structured_data:
                extra["structured_data"] = structured_data
                kwargs["extra"] = extra

            return msg, kwargs

    return StructuredLoggerAdapter(base_logger, {})


# Initialize default configuration
_initialized = False


def ensure_initialized() -> None:
    """Ensure logging is initialized with default configuration."""
    global _initialized
    if not _initialized:
        configure_logging(log_level="WARNING")
        _initialized = True


# Auto-initialize on import
ensure_initialized()
