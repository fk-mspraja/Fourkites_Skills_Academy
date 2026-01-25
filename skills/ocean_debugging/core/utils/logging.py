"""Structured logging for Ocean Debugging Agent"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import json


class StructuredFormatter(logging.Formatter):
    """JSON-structured log formatter"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class PrettyFormatter(logging.Formatter):
    """Human-readable log formatter for CLI output"""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        reset = self.COLORS["RESET"]

        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        level = record.levelname[:4]

        message = record.getMessage()

        # Format extra data if present
        extra = ""
        if hasattr(record, "extra_data") and record.extra_data:
            extra_parts = [f"{k}={v}" for k, v in record.extra_data.items()]
            extra = f" [{', '.join(extra_parts)}]"

        return f"{color}[{timestamp}] {level}{reset} {message}{extra}"


class AgentLogger(logging.Logger):
    """Custom logger with structured logging support"""

    def __init__(self, name: str, level: int = logging.NOTSET):
        super().__init__(name, level)

    def _log_with_extra(
        self,
        level: int,
        msg: str,
        args: tuple,
        extra_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log with extra structured data"""
        if extra_data:
            kwargs["extra"] = {"extra_data": extra_data}
        super()._log(level, msg, args, **kwargs)

    def info_with_data(self, msg: str, **extra_data):
        """Log info with structured data"""
        self._log_with_extra(logging.INFO, msg, (), extra_data)

    def debug_with_data(self, msg: str, **extra_data):
        """Log debug with structured data"""
        self._log_with_extra(logging.DEBUG, msg, (), extra_data)

    def warning_with_data(self, msg: str, **extra_data):
        """Log warning with structured data"""
        self._log_with_extra(logging.WARNING, msg, (), extra_data)

    def error_with_data(self, msg: str, **extra_data):
        """Log error with structured data"""
        self._log_with_extra(logging.ERROR, msg, (), extra_data)


def setup_logging(
    level: str = "INFO",
    json_output: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Set up logging for the Ocean Debugging Agent.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_output: Use JSON format (for production/log aggregation)
        log_file: Optional file path to write logs
    """
    # Set custom logger class
    logging.setLoggerClass(AgentLogger)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if json_output:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(PrettyFormatter())
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> AgentLogger:
    """Get a logger instance for a module"""
    return logging.getLogger(name)
