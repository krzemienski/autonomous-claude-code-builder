"""
Logging Configuration
=====================

Simple logging setup for acli.
"""

import logging
import sys


def get_logger(name: str = "acli") -> logging.Logger:
    """Get or create a logger instance."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        # Console handler
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.INFO)

        # Format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


# Default logger instance
logger = get_logger()
