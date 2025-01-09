import os
from unittest.mock import patch

from src.price_monitor.utils.clock import today_dashed_str
from src.price_monitor.utils.logger import init_logging_handler


@patch("src.price_monitor.utils.logger.logger")
def test_init_logging_handler_when_file_loging_set_then_create_file_logging(
    mock_logger,
):
    config = {"output": {"logs_directory": "logs/"}}
    os.environ["PM_FILE_LOGGING"] = "true"
    os.environ["PM_LOGURU_LEVEL"] = "INFO"
    init_logging_handler(config)
    mock_logger.add.assert_called_with(
        f"logs//price-monitor-{today_dashed_str()}.log",
        format="{time} {level} {name}:{function}:{line} - {message}",
        level="INFO",
    )
