"""Structured logging configuration for TypeMind AI."""

import logging
import sys
from typing import Optional


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """Configure and return the root logger for the application.

    Args:
        log_level: Optional log level override (e.g. 'DEBUG', 'INFO', 'WARNING').

    Returns:
        logging.Logger: Configured application logger instance.
    """
    level_name = (log_level or "INFO").upper()
    numeric_level = getattr(logging, level_name, logging.INFO)

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Avoid duplicate handlers if setup_logging is called multiple times
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))

    root_logger.setLevel(numeric_level)

    # Set specific logger for typemind
    logger = logging.getLogger("typemind")
    logger.setLevel(numeric_level)
    return logger
