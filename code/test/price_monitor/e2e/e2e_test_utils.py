import csv
import os
import shutil
from pathlib import Path

import fastavro
from assertpy import assert_that
from typer.testing import CliRunner

from src.price_monitor.main import app
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.utils.clock import (
    today_dashed_str_with_key,
)
from test.price_monitor.e2e.e2e_test_constants import (
    CONFIG_FILE_PATH,
    DATA_DIR,
    SAMPLE_DATA_DIR,
    PRICES_FILE_NAME,
    YESTERDAY_DIR,
    FINANCE_PRICES_FILE_NAME,
    DATA_QUALITY_CONFIG_FILE_PATH,
)

runner = CliRunner()


# TODO: Refactor this and maybe just switch to running data quality checks
def verify_output_files(
    market: Market, vendor: Vendor, file_name: str, file_type: str = "csv"
):
    records = read_file_to_list(
        file_type=file_type, file_name=file_name, market=market, vendor=vendor
    )

    assert_that(records).is_not_empty()

    for record in records:
        assert_that(record["vendor"]).is_equal_to(vendor)
        assert_that(record["market"]).is_equal_to(market)

        if file_name == "prices":
            assert_that(float(record["gross_list_price"])).is_positive()
            assert_that(float(record["net_list_price"])).is_positive()
            assert_that(record["is_current"]).is_true()

        if file_name == "finance_options":
            # We are only scraping complete data for PCP for now
            if record["contract_type"] == "PCP":
                assert_that(float(record["otr"])).is_positive()
                assert_that(record["is_current"]).is_true()


def read_file_to_list(
    file_type: str, file_name: str, vendor: Vendor, market: Market
) -> list[dict]:
    if file_type == "csv":
        with open(
            f"{DATA_DIR}/{today_dashed_str_with_key()}/{file_name}.csv", "r"
        ) as file:
            records = list(csv.DictReader(file))
    else:
        with open(
            f"{DATA_DIR}/{today_dashed_str_with_key()}/{file_name}.avro", "rb"
        ) as file:
            records = list(fastavro.reader(file))

    # This is required when reading the changelog file
    # because it will contain entries for other "missing" vendors
    return list(
        filter(lambda x: (x["vendor"] == vendor and x["market"] == market), records)
    )


def run_price_scraper_and_assert_successful(
    market: str, vendor: str, file_type: str = "csv"
):
    result = runner.invoke(
        app,
        [
            "run-scraper",
            "--market",
            market,
            "--scraper",
            vendor,
            "--config-file",
            CONFIG_FILE_PATH,
            "--output",
            file_type,
            "--directory",
            DATA_DIR,
        ],
    )

    assert_that(result).has_exit_code(0)


def run_compare_and_assert_successful(file_type: str = "csv"):
    result = runner.invoke(
        app,
        [
            "run-compare",
            "--config-file",
            CONFIG_FILE_PATH,
            "--output",
            file_type,
            "--directory",
            DATA_DIR,
        ],
    )

    assert_that(result).has_exit_code(0)


def run_finance_scraper_and_assert_successful(
    market: str, vendor: str, file_type: str = "csv"
):
    result = runner.invoke(
        app,
        [
            "run-finance-scraper",
            "--market",
            market,
            "--scraper",
            vendor,
            "--config-file",
            CONFIG_FILE_PATH,
            "--output",
            file_type,
            "--directory",
            DATA_DIR,
        ],
    )

    assert_that(result).has_exit_code(0)


def run_data_quality_checks_and_assert_successful():
    result = runner.invoke(
        app,
        [
            "check-data-quality",
            "--config-file",
            DATA_QUALITY_CONFIG_FILE_PATH,
            "--directory",
            DATA_DIR,
        ],
    )

    assert_that(result).has_exit_code(0)


def add_yesterday_price_data() -> None:
    shutil.copy(Path(SAMPLE_DATA_DIR) / PRICES_FILE_NAME, YESTERDAY_DIR)


def remove_yesterday_price_data() -> None:
    os.remove(Path(YESTERDAY_DIR) / PRICES_FILE_NAME)


def add_today_finance_data() -> None:
    shutil.copy(Path(SAMPLE_DATA_DIR) / FINANCE_PRICES_FILE_NAME, YESTERDAY_DIR)


def remove_today_finance_data() -> None:
    os.remove(Path(YESTERDAY_DIR) / FINANCE_PRICES_FILE_NAME)
