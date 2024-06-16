import sys

from loguru import logger

from planner.config import config

DEFAULT_LOGGING_LEVEL = "INFO"


# --------------------------------------------------


def add_terminal_sink():
    """Setup a free text logging sink to stdout"""
    level = config.get("logging_level", default=DEFAULT_LOGGING_LEVEL).upper()
    logger.add(
        sys.stderr,
        format="<level>{message}</level>",
        level=level,
        colorize=True,
    )


def add_file_sink():
    """Setup a free text logging sink to stdout"""
    level = config.get("logging_level", default=DEFAULT_LOGGING_LEVEL).upper()
    logger.add(
        "logs.txt",
        format="{message}",
        level=level,
    )


# --------------------------------------------------


logger.remove()  # remove default sink
if config.get("logging_level") is not None:
    add_terminal_sink()
