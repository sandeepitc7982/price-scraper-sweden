import glob
import os
from pathlib import Path
from test.price_monitor.utils.test_data_builder import (
    create_test_difference_item,
    create_test_option_price_difference_item,
)

import pytest

from src.price_monitor.model.difference_item import DifferenceItem, DifferenceReason
from src.price_monitor.model.option_price_difference_item import (
    OptionPriceDifferenceItem,
)
from src.price_monitor.model.price_difference_item import PriceDifferenceItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.difference_item_repository import (
    DifferenceItemRepository,
)
from src.price_monitor.utils.clock import today_dashed_str, today_dashed_str_with_key
from src.price_monitor.utils.csv_helper import load_csv_for_difference_item_loader

TEST_DATA_DIR = f"{Path(__file__).parent}/data"
FILE_NAME = "test_changelog"
ITEMS = [
    DifferenceItem(
        recorded_at=today_dashed_str(),
        vendor=Vendor.TESLA,
        series="my_series",
        model_range_code="TSTR",
        model_range_description="test range",
        model_code="MDL",
        model_description="test model",
        line_code="stand",
        line_description="standard",
        old_value="4454",
        new_value="5000",
        reason=DifferenceReason.NEW_LINE,
        market=Market.DE,
    ),
    DifferenceItem(
        recorded_at=today_dashed_str(),
        vendor=Vendor.BMW,
        series="my_series",
        model_range_code="TSTR",
        model_range_description="test range",
        model_code="MDL",
        model_description="test model",
        line_code="stand",
        line_description="standard",
        old_value="4454",
        new_value="5000",
        reason=DifferenceReason.PRICE_CHANGE,
        market=Market.DE,
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
            "file_type": "csv",
        }
    }
    repository = DifferenceItemRepository(config=config)

    repository.save(ITEMS, DifferenceItem)

    assert (
        repository.load(
            date=today_dashed_str_with_key(), difference_item_class=DifferenceItem
        )
        == ITEMS
    )


def test_save_and_load_avro():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "file_type": "avro",
        }
    }
    repository = DifferenceItemRepository(config=config)
    repository.save(ITEMS, DifferenceItem)

    assert (
        repository.load(
            date=today_dashed_str_with_key(), difference_item_class=DifferenceItem
        )
        == ITEMS
    )


def test_save_csv_load_avro():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "file_type": "csv",
        }
    }
    repository = DifferenceItemRepository(config)
    repository.save(ITEMS, DifferenceItem)

    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "file_type": "avro",
        }
    }

    repository.save(ITEMS, DifferenceItem)

    assert (
        repository.load(
            date=today_dashed_str_with_key(), difference_item_class=DifferenceItem
        )
        == ITEMS
    )


def test_return_empty_list_for_no_file():
    repository = DifferenceItemRepository(
        config={
            "output": {
                "directory": TEST_DATA_DIR,
                "differences_filename": "not_a_real_file",
            }
        }
    )

    assert (
        repository.load(date="19990909", difference_item_class=PriceDifferenceItem)
        == []
    )


def test_save_avro_load_csv():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "file_type": "avro",
        }
    }
    repository = DifferenceItemRepository(config=config)

    repository.save(ITEMS, DifferenceItem)

    assert (
        repository.load(
            date=today_dashed_str_with_key(), difference_item_class=DifferenceItem
        )
        == ITEMS
    )


def test_save_price_diffs():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": "price_changelog",
            "file_type": "avro",
        }
    }

    repository = DifferenceItemRepository(config)

    repository.save([create_test_difference_item()], PriceDifferenceItem)

    assert repository.load(
        date=today_dashed_str_with_key(),
        difference_item_class=PriceDifferenceItem,
    ) == [create_test_difference_item()]


def test_saves_empty_file_when_empty_list():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": "price_changelog",
            "file_type": "avro",
        }
    }

    repository = DifferenceItemRepository(config)
    repository.save([], PriceDifferenceItem)

    assert (
        repository.load(
            date=today_dashed_str_with_key(),
            difference_item_class=PriceDifferenceItem,
        )
        == []
    )


def test_when_we_save_difference_item_into_repository_then_we_exclude_the_difference_item_with_reason_option_included():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "file_type": "avro",
        }
    }
    ITEMS.append(
        DifferenceItem(
            recorded_at=today_dashed_str(),
            vendor=Vendor.BMW,
            series="my_series",
            model_range_code="TSTR",
            model_range_description="test range",
            model_code="MDL",
            model_description="test model",
            line_code="stand",
            line_description="standard",
            old_value="",
            new_value="A234",
            reason=DifferenceReason.OPTION_INCLUDED,
            market=Market.DE,
        ),
    )
    repository = DifferenceItemRepository(config=config)

    repository.save(ITEMS, DifferenceItem)

    ITEMS.pop(-1)

    assert (
        repository.load(
            date=today_dashed_str_with_key(), difference_item_class=DifferenceItem
        )
        == ITEMS
    )


def test_when_we_save_difference_item_into_repository_then_we_exclude_the_difference_item_with_reason_option_excluded():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "file_type": "avro",
        }
    }
    ITEMS.append(
        DifferenceItem(
            recorded_at=today_dashed_str(),
            vendor=Vendor.BMW,
            series="my_series",
            model_range_code="TSTR",
            model_range_description="test range",
            model_code="MDL",
            model_description="test model",
            line_code="stand",
            line_description="standard",
            old_value="",
            new_value="A234",
            reason=DifferenceReason.OPTION_EXCLUDED,
            market=Market.DE,
        ),
    )
    repository = DifferenceItemRepository(config=config)

    repository.save(ITEMS, DifferenceItem)

    ITEMS.pop(-1)

    assert (
        repository.load(
            date=today_dashed_str_with_key(), difference_item_class=DifferenceItem
        )
        == ITEMS
    )


def test__load_csv_returns_empty_list_when_differences_file_name_is_empty():
    os.makedirs(f"{TEST_DATA_DIR}/{today_dashed_str_with_key()}", exist_ok=True)
    with open(f"{TEST_DATA_DIR}/{today_dashed_str_with_key()}/changelog.csv", "w") as f:
        f.write(
            "vendor,series,model_range_code,model_range_description,model_code,model_description,line_code,line_description,old_value,new_value,reason,market\n"
        )
    actual_result = load_csv_for_difference_item_loader(
        differences_filename="changelog",
        target_dir=f"{TEST_DATA_DIR}/{today_dashed_str_with_key()}",
        difference_item_class=DifferenceItem,
    )
    expected_result = []
    assert actual_result == expected_result


def test_when_we_save_difference_item_into_repository_then_we_exclude_the_difference_item_with_reason_option_price_change():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": FILE_NAME,
            "file_type": "avro",
        }
    }
    ITEMS.append(
        DifferenceItem(
            recorded_at=today_dashed_str(),
            vendor=Vendor.BMW,
            series="my_series",
            model_range_code="TSTR",
            model_range_description="test range",
            model_code="MDL",
            model_description="test model",
            line_code="stand",
            line_description="standard",
            old_value="",
            new_value="A234",
            reason=DifferenceReason.OPTION_PRICE_CHANGE,
            market=Market.DE,
        ),
    )
    repository = DifferenceItemRepository(config=config)

    repository.save(ITEMS, DifferenceItem)

    ITEMS.pop(-1)

    assert (
        repository.load(
            date=today_dashed_str_with_key(), difference_item_class=DifferenceItem
        )
        == ITEMS
    )


def test_save_option_price_diffs():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "differences_filename": "option_price_changelog",
            "file_type": "avro",
        }
    }

    repository = DifferenceItemRepository(config)

    repository.save(
        [create_test_option_price_difference_item()], OptionPriceDifferenceItem
    )

    assert repository.load(
        date=today_dashed_str_with_key(),
        difference_item_class=OptionPriceDifferenceItem,
    ) == [create_test_option_price_difference_item()]
