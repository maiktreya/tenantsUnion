import logging
import sys
import os


def setup_logging():
    """
    Configures a logger that sets its level based on the DEV_MODE
    environment variable.
    """
    # Check the environment variable. Treat 'true', '1', 't' as debug mode.
    is_dev_mode = os.environ.get("DEV_MODE", "False").lower() in ("true", "1", "t")
    log_level = logging.DEBUG if is_dev_mode else logging.INFO

    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Avoid adding handlers more than once
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logging.info(
        f"Logging initialized in {'DEVELOPMENT' if is_dev_mode else 'PRODUCTION'} mode (level: {logging.getLevelName(log_level)})."
    )
