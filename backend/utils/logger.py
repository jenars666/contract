import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOGGER_NAME = "smartpatch"
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.INFO: "\033[94m",
        logging.WARNING: "\033[93m",
        logging.ERROR: "\033[91m",
        logging.CRITICAL: "\033[91m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        color = self.COLORS.get(record.levelno, "")
        return f"{color}{base}{self.RESET}" if color else base


def _configure_base_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(ColorFormatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console)

    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=os.path.join("logs", "smartpatch.log"),
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

    return logger


def get_logger(module_name: str) -> logging.Logger:
    base = _configure_base_logger()
    return base.getChild(module_name)


logger = get_logger("app")
