import sys

from loguru import logger

from planner.config import config

DEFAULT_LOGGING_LEVEL = "INFO"


# --------------------------------------------------


def add_terminal_sink():
    """Setup a free text logging sink to stdout"""
    level = config.get("logging_level", default=DEFAULT_LOGGING_LEVEL).upper()
    logger.add(
        sys.stdout,
        format="<level>{message}</level>",
        level=level,
        colorize=True,
    )


# --------------------------------------------------


logger.remove()  # remove default sink
add_terminal_sink()
