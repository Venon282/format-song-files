import logging
import sys
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """
    Custom Formatter to add colors to the levelname based on the log level.
    """

    # ANSI Escape Sequences
    BLUE = "\x1b[34m"
    GREEN = "\x1b[32m"
    ORANGE = "\x1b[38;5;208m"  # 8-bit color for true orange
    RED = "\x1b[31m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    # Mapping levels to your requested colors
    COLORS = {
        logging.DEBUG: BLUE,
        logging.INFO: GREEN,
        logging.WARNING: ORANGE,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED,
    }

    def __init__(self, fmt: str):
        super().__init__()
        self.fmt = fmt
        self._plain_formatter = logging.Formatter(self.fmt, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record):
        # Apply color to the levelname
        level_color = self.COLORS.get(record.levelno, self.RESET)

        # Save original levelname to restore it later (so file logs stay clean)
        orig_levelname = record.levelname
        record.levelname = f"{level_color}{orig_levelname}{self.RESET}"

        result = self._plain_formatter.format(record)

        # Restore original levelname for other handlers (like file logging)
        record.levelname = orig_levelname
        return result

def getLogger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_str: Optional[str] = "%(levelname)s - %(name)s - %(asctime)s  - %(message)s"
) -> logging.Logger:
    """
    Configures and returns a logger instance.

    Args:
        name: Name of the logger (usually __name__).
        level: Logging level (e.g., logging.INFO).
        log_file: Optional path to save logs to a file.
    """
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(level)

    # Console Handler (Colored)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(format_str))
    logger.addHandler(console_handler)

    # File Handler (Plain Text)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(file_handler)

    return logger