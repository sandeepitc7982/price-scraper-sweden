import glob
import os
from pathlib import Path

import pytest

from src.price_monitor.finance_comparer.difference_finance_item import (
    DifferenceFinanceItem,
    FinanceItemDifferenceReason,
)
from src.price_monitor.model.vendor import Vendor, Market
from src.price_monitor.finance_comparer.difference_finance_item_repository import (
    DifferenceFinanceItemRepository,
)
from src.price_monitor.utils.clock import today_dashed_str_with_key
from test.price_monitor.utils.test_data_builder import (
    create_difference_finance_line_item,
)

TEST_DATA_DIR = f"{Path(__file__).parent}/data"
FILE_NAME = "test_changelog"

ITEMS = [
    create_difference_finance_line_item(
        reason=FinanceItemDifferenceReason.PCP_OTR_CHANGED,
        old_value=123,
        new_value=321,
        vendor=Vendor.AUDI,
        market=Market.UK,
    ),
    create_difference_finance_line_item(
        reason=FinanceItemDifferenceReason.PCP_FIXED_ROI_CHANGED,
        old_value=9.0,
        new_value=8.0,
        vendor=Vendor.AUDI,
        market=Market.UK,
    ),
]


@pytest.fixture(scope="class", autouse=True)
def setup():
    yield

    for file in glob.glob(f"{TEST_DATA_DIR}/{today_dashed_str_with_key()}/*"):
        os.remove(file)

    if os.path.exists(f"{TEST_DATA_DIR}/{today_dashed_str_with_key()}"):
        os.rmdir(f"{TEST_DATA_DIR}/{today_dashed_str_with_key()}")


def test_save_and_load_csv():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "finance_options_filename": "",
            "file_type": "csv",
        }
    }
    repository = DifferenceFinanceItemRepository(config=config)

    repository.save(ITEMS, DifferenceFinanceItem)

    assert (
        repository.load(
            date=today_dashed_str_with_key(),
            difference_item_class=DifferenceFinanceItem,
        )
        == ITEMS
    )


def test_save_and_load_avro():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "finance_options_filename": "Finance_options",
            "file_type": "avro",
        }
    }
    repository = DifferenceFinanceItemRepository(config=config)
    repository.save(ITEMS, DifferenceFinanceItem)

    assert (
        repository.load(
            date=today_dashed_str_with_key(),
            difference_item_class=DifferenceFinanceItem,
        )
        == ITEMS
    )


def test_save_csv_load_avro():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "finance_options_filename": "",
            "file_type": "csv",
        }
    }
    repository = DifferenceFinanceItemRepository(config=config)
    repository.save(ITEMS, DifferenceFinanceItem)

    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "finance_options_filename": "",
            "file_type": "avro",
        }
    }

    repository.save(ITEMS, DifferenceFinanceItem)

    assert (
        repository.load(
            date=today_dashed_str_with_key(),
            difference_item_class=DifferenceFinanceItem,
        )
        == ITEMS
    )


def test_return_empty_list_for_no_file():
    repository = DifferenceFinanceItemRepository(
        config={
            "output": {
                "directory": TEST_DATA_DIR,
                "differences_filename": "not_a_real_file",
                "finance_options_filename": "",
            }
        }
    )

    assert (
        repository.load(date="19990909", difference_item_class=DifferenceFinanceItem)
        == []
    )


def test_save_avro_load_csv():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "finance_options_filename": "",
            "file_type": "avro",
        }
    }
    repository = DifferenceFinanceItemRepository(config=config)

    repository.save(ITEMS, DifferenceFinanceItem)

    assert (
        repository.load(
            date=today_dashed_str_with_key(),
            difference_item_class=DifferenceFinanceItem,
        )
        == ITEMS
    )


def test_saves_empty_file_when_empty_list():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "finance_options_filename": "",
            "file_type": "avro",
        }
    }

    repository = DifferenceFinanceItemRepository(config)
    repository.save([], DifferenceFinanceItem)

    assert (
        repository.load(
            date=today_dashed_str_with_key(),
            difference_item_class=DifferenceFinanceItem,
        )
        == []
    )


def test_save_options_difference():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "finance_options_filename": "",
            "file_type": "avro",
        }
    }

    repository = DifferenceFinanceItemRepository(config)

    repository.save(
        [
            create_difference_finance_line_item(
                reason=FinanceItemDifferenceReason.PCP_OTR_CHANGED,
                old_value=123,
                new_value=321,
                vendor=Vendor.AUDI,
                market=Market.UK,
            )
        ],
        DifferenceFinanceItem,
    )

    assert repository.load(
        date=today_dashed_str_with_key(),
        difference_item_class=DifferenceFinanceItem,
    ) == [
        create_difference_finance_line_item(
            reason=FinanceItemDifferenceReason.PCP_OTR_CHANGED,
            old_value=123,
            new_value=321,
            vendor=Vendor.AUDI,
            market=Market.UK,
        )
    ]
