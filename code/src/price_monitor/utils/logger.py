import os

import google.cloud.logging
from google.cloud.logging_v2.handlers import CloudLoggingHandler
from loguru import logger

from src.price_monitor.utils.clock import today_dashed_str

log_level = os.getenv("LOGURU_LEVEL", "INFO")


def init_gcp_logging():
    client = google.cloud.logging.Client()
    handler = CloudLoggingHandler(client)
    logger.add(handler, level=log_level)


def init_logging_handler(config):

    if os.getenv("PM_GCP_LOGGING") == "true":
        init_gcp_logging()

    # Saving logs to price-monitor-{date}.log in configured directory.
    if os.getenv("PM_FILE_LOGGING") == "true":
        log_folder = config["output"].get("logs_directory", "logs/")
        logger.add(
            log_folder + f"/price-monitor-{today_dashed_str()}.log",
            format="{time} {level} {name}:{function}:{line} - {message}",
            level=log_level,
        )
