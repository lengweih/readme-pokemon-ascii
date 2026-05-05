import logging
import sys

LOGGER_NAME = "readme_pokemon_ascii"
LOG_FORMAT = "%(levelname)s %(name)s: %(message)s"
QUIET_LOGGERS = ("httpx", "httpcore")


def configure_logging() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    for logger_name in QUIET_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    return logger


def get_logger(name: str) -> logging.Logger:
    return configure_logging().getChild(name)
