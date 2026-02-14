import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(logger_name, log_file, log_level_env, backup_count=10, max_bytes=20000000):
    """Setup a logger with rotating file handler only (no console output)."""
    log_dir = os.getenv("LOG_DIRECTORY", "./")
    logger_file_path = os.path.join(str(log_dir), log_file)

    # Set log level from environment variable
    log_level_dict = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = log_level_dict.get(log_level_env.upper(), logging.INFO)

    # Get or create the logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers
    if not logger.handlers:
        # Rotating file handler only
        file_handler = RotatingFileHandler(
            logger_file_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(filename)s] [%(lineno)s:%(funcName)5s()] %(message)s",
            datefmt="%Y-%b-%d %H:%M:%S"
        ))
        logger.addHandler(file_handler)

    return logger, log_level


# Initialize LOGGER
log_level_env = os.getenv("LOG_LEVEL", "INFO")
LOGGER, LOG_LEVEL = setup_logger("RESTAURANT_TABLE_LOGGER", "whatsapp.log", log_level_env)
