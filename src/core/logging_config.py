"""
Logging configuration with structured logging support.
"""

import logging
import sys

from src.core.config import settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that adds structured information to log records.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with additional context.

        Args:
            record: Log record to format

        Returns:
            Formatted log string
        """
        # Add custom fields if they exist
        if not hasattr(record, "request_id"):
            record.request_id = "-"

        # Format the message
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - " "[%(request_id)s] - %(message)s"
        )

        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging() -> None:
    """
    Configure the application logger.
    """
    # Get log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(StructuredFormatter())

    # Add handler to root logger
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Name for the logger (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
