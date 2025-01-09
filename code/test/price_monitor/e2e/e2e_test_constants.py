from pathlib import Path
from src.price_monitor.utils.clock import (
    today_dashed_str_with_key,
    yesterday_dashed_str_with_key,
)

DATA_DIR = Path(__file__).parent.parent / "data"
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "sample"
CONFIG_DIR = Path(__file__).parent.parent / "config"

CONFIG_FILE_PATH = CONFIG_DIR / "config.json"
DATA_QUALITY_CONFIG_FILE_PATH = CONFIG_DIR / "data_quality_config.json"
YESTERDAY_DIR = DATA_DIR / yesterday_dashed_str_with_key()
TODAY_DIR = DATA_DIR / today_dashed_str_with_key()
PRICES_FILE_NAME = "prices.avro"
FINANCE_PRICES_FILE_NAME = "finance_options.avro"
