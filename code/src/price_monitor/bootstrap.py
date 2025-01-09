import json
from pathlib import Path

from src.price_monitor.utils.adls import AzureDataLakeStorage
from src.price_monitor.utils.logger import init_logging_handler


def __init_config(
    config_file: Path,
    scraper: str = None,
    finance_scraper: str = None,
    market: str = None,
    output: str = None,
    directory: str = None,
) -> dict:
    with open(config_file, "r") as file:
        config = json.load(file)

    # TODO: Make config params more flexible to work with any combination provided
    if scraper and market:
        config["scraper"]["enabled"] = {scraper: [market]}
    if finance_scraper and market:
        config["finance_scraper"]["enabled"] = {finance_scraper: [market]}
    if output:
        config["output"]["file_type"] = output
    if directory:
        config["output"]["directory"] = directory

    return config


def initialize(
    config_file,
    scraper: str = None,
    finance_scraper: str = None,
    market: str = None,
    output: str = None,
    directory: str = None,
):
    # Initialising config
    config = __init_config(
        config_file=config_file,
        finance_scraper=finance_scraper,
        scraper=scraper,
        market=market,
        output=output,
        directory=directory,
    )
    # Initialising logging handlers(GCP/File Based)
    init_logging_handler(config)

    adls = initialize_adls(config)

    return config, adls


def initialize_adls(config):
    adls = None
    if config.get("adls", {}).get("enabled", False):
        adls = AzureDataLakeStorage(config)
        adls.download_folder_from_adls()

    return adls


def finalize(adls):
    if adls:
        adls.upload_folder_to_adls()
