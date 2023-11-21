"""Logging capabilities."""

import functools
import logging
from logging.config import dictConfig

from trickster.config import get_config


@functools.cache
def get_logger() -> logging.Logger:
    """Get configured logger to be used within the app."""
    config = get_config()
    dictConfig(config.logging)
    return logging.getLogger('trickster')
