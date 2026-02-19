"""
Structured Logging Utility - Consistent logging across the application
"""

import logging
import sys
from typing import Any, Dict, Optional
import json
from datetime import datetime


class StructuredLogger:
    """
    Structured logger that outputs JSON-formatted logs for production.
    Falls back to standard logging in development.
    """

    def __init__(self, name: str, structured: bool = False):
        self.logger = logging.getLogger(name)
        self.structured = structured

    def _format_message(self, level: str, message: str, **context) -> str:
        """Format message with context as JSON if structured mode enabled."""
        if not self.structured:
            if context:
                ctx_str = " | " + " | ".join(f"{k}={v}" for k, v in context.items())
                return f"{message}{ctx_str}"
            return message

        # Structured JSON format
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "logger": self.logger.name,
            **context
        }
        return json.dumps(log_entry)

    def debug(self, message: str, **context):
        """Log debug message with optional context."""
        self.logger.debug(self._format_message("DEBUG", message, **context))

    def info(self, message: str, **context):
        """Log info message with optional context."""
        self.logger.info(self._format_message("INFO", message, **context))

    def warning(self, message: str, **context):
        """Log warning message with optional context."""
        self.logger.warning(self._format_message("WARNING", message, **context))

    def error(self, message: str, exc_info: bool = False, **context):
        """Log error message with optional exception info and context."""
        self.logger.error(
            self._format_message("ERROR", message, **context),
            exc_info=exc_info
        )

    def critical(self, message: str, exc_info: bool = False, **context):
        """Log critical message with optional exception info and context."""
        self.logger.critical(
            self._format_message("CRITICAL", message, **context),
            exc_info=exc_info
        )


def get_logger(name: str, structured: bool = False) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)
        structured: Enable JSON structured logging (for production)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, structured=structured)


def configure_logging(level: str = "INFO", structured: bool = False):
    """
    Configure global logging settings.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Enable JSON structured logging
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    if structured:
        # JSON format for production
        logging.basicConfig(
            level=log_level,
            format="%(message)s",  # Just the message (already JSON)
            stream=sys.stderr,
            force=True,
        )
    else:
        # Human-readable format for development
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stderr,
            force=True,
        )
