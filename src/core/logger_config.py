import logging
import sys

class ColorFormatter(logging.Formatter):
    """A logging formatter that adds color to the output."""

    COLORS = {
        "DEBUG": "\033[94m",    # Blue
        "INFO": "\033[92m",     # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",    # Red
        "CRITICAL": "\033[91;1m", # Bold Red
        "RESET": "\033[0m",
    }

    def format(self, record):
        log_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, '')}{log_message}{self.COLORS['RESET']}"

def setup_logger(debug: bool = False):
    """
    Sets up a colored logger.

    Args:
        debug: If True, sets the logging level to DEBUG. Otherwise, INFO.
    """
    level = logging.DEBUG if debug else logging.INFO
    formatter = ColorFormatter(
        "[%(asctime)s] [%(levelname)-8s] [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers and add our new one
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Set the logging level for other libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)

    return root_logger