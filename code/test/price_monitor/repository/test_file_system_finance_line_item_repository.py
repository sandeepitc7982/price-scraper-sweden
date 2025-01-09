import glob
import os
from pathlib import Path
from test.price_monitor.utils.test_data_builder import create_test_finance_line_item

import pytest

from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.vendor import Currency, Market, Vendor
from src.price_monitor.repository.finance_item_repository import (
    FileSystemFinanceLineItemRepository,
)
from src.price_monitor.utils.clock import (
    today_dashed_str_with_key,
    yesterday_dashed_str_with_key,
)

TEST_DATA_DIR = f"{Path(__file__).parent}/data"
FILE_NAME = "test_finance_options"
ITEMS = [
    create_test_finance_line_item(),
    create_test_finance_line_item(
        vendor=Vendor.BMW,
        market=Market.UK,
        series="series",
        model_range_code="model_range_code",
        model_code="model_code",
        line_code="line_code",
    ),
    create_test_finance_line_item(
        vendor=Vendor.BMW,
        market=Market.UK,
        series="series",
        model_range_code="model_range_code1",
        model_code="model_code1",
        line_code="line_code1",
    ),
]


@pytest.fixture(scope="class", autouse=True)
def setup():
    yield
    for file in glob.glob(
        f"{TEST_DATA_DIR}/{today_dashed_str_with_key()}/{FILE_NAME}.*"
    ):
        os.remove(file)
    for file in glob.glob(
        f"{TEST_DATA_DIR}/{yesterday_dashed_str_with_key()}/{FILE_NAME}.*"
    ):
        os.remove(file)
    if os.path.exists(f"{TEST_DATA_DIR}/{today_dashed_str_with_key()}"):
        os.rmdir(f"{TEST_DATA_DIR}/{today_dashed_str_with_key()}")

    if os.path.exists(f"{TEST_DATA_DIR}/{yesterday_dashed_str_with_key()}"):
        os.rmdir(f"{TEST_DATA_DIR}/{yesterday_dashed_str_with_key()}")


def test_save_and_load_avro():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "finance_options_filename": FILE_NAME,
            "file_type": "avro",
        }
    }
    repository = FileSystemFinanceLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load(date=today_dashed_str_with_key()) == ITEMS


def test_save_and_load_csv():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "finance_options_filename": FILE_NAME,
            "file_type": "csv",
        }
    }
    repository = FileSystemFinanceLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load(date=today_dashed_str_with_key()) == ITEMS


def test_save_and_load_default_when_file_type_not_provided():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "finance_options_filename": FILE_NAME,
        }
    }
    repository = FileSystemFinanceLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load(date=today_dashed_str_with_key()) == ITEMS


def test_save_and_load_dual():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "finance_options_filename": FILE_NAME,
            "file_type": "dual",
        }
    }
    repository = FileSystemFinanceLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load(date=today_dashed_str_with_key()) == ITEMS


def test_update_finance_line_items_when_data_is_already_present_for_scraped_data_then_data_should_be_replaced():
    finance_line_item = create_test_finance_line_item(model_code="model_code")
    finance_line_item1 = create_test_finance_line_item(model_code="model_code1")
    expected_finance_line_items = [finance_line_item, finance_line_item1]
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "finance_options_filename": FILE_NAME,
            "file_type": "avro",
        },
        "scraper": {"enabled": {"audi": ["UK"]}},
    }
    existing_finance_line_items = [finance_line_item]
    new_finance_line_items = [finance_line_item1]
    finance_line_item_repository = FileSystemFinanceLineItemRepository(config=config)

    finance_line_item_repository.update_finance_line_item(
        existing_finance_line_items, new_finance_line_items, config
    )
    actual_finance_line_items = finance_line_item_repository.load(
        date=today_dashed_str_with_key()
    )

    assert actual_finance_line_items == expected_finance_line_items


def test_update_finance_line_items_when_data_is_not_present_for_that_market_then_data_should_be_appended():
    finance_line_item = create_test_finance_line_item(model_code="model_code")
    finance_line_item1 = create_test_finance_line_item(
        market=Market.UK, model_code="model_code1"
    )
    expected_finance_line_items = [finance_line_item, finance_line_item1]
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "finance_options_filename": FILE_NAME,
            "file_type": "avro",
        },
        "scraper": {"enabled": {"audi": ["UK"]}},
    }
    existing_finance_line_items = [finance_line_item]
    new_finance_line_items = [finance_line_item1]
    finance_line_item_repository = FileSystemFinanceLineItemRepository(config=config)

    finance_line_item_repository.update_finance_line_item(
        existing_finance_line_items, new_finance_line_items, config
    )
    actual_finance_line_items = finance_line_item_repository.load(
        date=today_dashed_str_with_key()
    )

    assert actual_finance_line_items == expected_finance_line_items


def test_load_market():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "finance_options_filename": FILE_NAME,
            "file_type": "avro",
        },
        "scraper": {"enabled": {"audi": ["UK"]}},
    }
    repository = FileSystemFinanceLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load_market(
        date=today_dashed_str_with_key(), vendor=Vendor.AUDI, market=Market.DE
    ) == [create_test_finance_line_item()]


def test_load_model_filter_by_model_range_description():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "finance_options_filename": FILE_NAME,
            "file_type": "avro",
        },
        "scraper": {"enabled": {"audi": ["UK"]}},
    }
    repository = FileSystemFinanceLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())
    item = create_test_finance_line_item()

    assert repository.load_model_filter_by_model_range_description(
        date=today_dashed_str_with_key(),
        vendor=item.vendor,
        market=item.market,
        model_range_description=item.model_range_description,
    ) == [item]


def test_load_model_filter_by_line_code():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "finance_options_filename": FILE_NAME,
            "file_type": "avro",
        },
        "scraper": {"enabled": {"bmw": ["UK"]}},
    }
    repository = FileSystemFinanceLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load_model_filter_by_line_code(
        date=today_dashed_str_with_key(),
        vendor=Vendor.BMW,
        market=Market.UK,
        model_range_code="model_range_code",
        model_code="model_code",
        line_code="line_code",
        series="series",
    ) == [ITEMS[1]]


def test_load_model_filter_by_series():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "finance_options_filename": FILE_NAME,
            "file_type": "avro",
        },
        "scraper": {"enabled": {"bmw": ["UK"]}},
    }
    repository = FileSystemFinanceLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert (
        repository.load_model_filter_by_series(
            date=today_dashed_str_with_key(),
            vendor=Vendor.BMW,
            market=Market.UK,
            series="series",
        )
        == ITEMS[1:3]
    )


def test_term_of_aggrement_datatype_in_avro():
    expected_term_of_aggrement_datatype = int

    with open(f"{TEST_DATA_DIR}/{FILE_NAME}.avro", "wb"):
        records: list[dict] = [line_item.asdict() for line_item in ITEMS]
        for record in records:
            actual_term_of_agreement_value = record["term_of_agreement"]

    assert isinstance(
        actual_term_of_agreement_value, expected_term_of_aggrement_datatype
    )


def test_term_of_aggrement_value_to_zero_if_not_in_record():
    expected_value = 0

    with open(f"{TEST_DATA_DIR}/{FILE_NAME}.avro", "wb"):
        records: list[dict] = [line_item.asdict() for line_item in ITEMS]
        for record in records:
            actual_value = record["term_of_agreement"]

    assert expected_value == actual_value


# This test needs to be re-worked (not fully completed)
def test_term_of_aggrement_read_from_past_throws_expecption():

    items = [
        create_test_finance_line_item(
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model Y",
            model_code="$MTY13",
            model_description="Model Y",
            line_code="$MTY13",
            line_description="Rear-Wheel Drive",
            contract_type="Business Contract Hire",
            term_of_agreement=0,
        ),
        FinanceLineItem(
            recorded_at="2024-08-20",
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model Y",
            model_code="$MTY13",
            model_description="Model Y",
            line_code="$MTY13",
            line_description="Rear-Wheel Drive",
            contract_type="PCP",
            monthly_rental_nlp=330.83,
            monthly_rental_glp=397.0,
            currency=Currency.UK,
            market=Market.UK,
            term_of_agreement=48,
        ),
        FinanceLineItem(
            recorded_at="2024-08-20",
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model Y",
            model_code="$MTY13",
            model_description="Model Y",
            line_code="$MTY13",
            line_description="Rear-Wheel Drive",
            contract_type="PCP",
            monthly_rental_nlp=330.83,
            monthly_rental_glp=397.0,
            currency=Currency.UK,
            market=Market.UK,
            term_of_agreement=48,
        ),
        FinanceLineItem(
            recorded_at="2024-08-20",
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model Y",
            model_code="$MTY13",
            model_description="Model Y",
            line_code="$MTY13",
            line_description="Rear-Wheel Drive",
            contract_type="PCP",
            monthly_rental_nlp=330.83,
            monthly_rental_glp=397.0,
            currency=Currency.UK,
            market=Market.UK,
            term_of_agreement=48,
        ),
        FinanceLineItem(
            recorded_at="2024-08-20",
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model Y",
            model_code="$MTY13",
            model_description="Model Y",
            line_code="$MTY13",
            line_description="Rear-Wheel Drive",
            contract_type="PCP",
            monthly_rental_nlp=330.83,
            monthly_rental_glp=397.0,
            currency=Currency.UK,
            market=Market.UK,
            term_of_agreement=48,
        ),
        FinanceLineItem(
            recorded_at="2024-08-20",
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model Y",
            model_code="$MTY13",
            model_description="Model Y",
            line_code="$MTY13",
            line_description="Rear-Wheel Drive",
            contract_type="PCP",
            monthly_rental_nlp=330.83,
            monthly_rental_glp=397.0,
            currency=Currency.UK,
            market=Market.UK,
            term_of_agreement=48,
        ),
        FinanceLineItem(
            recorded_at="2024-08-20",
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model Y",
            model_code="$MTY13",
            model_description="Model Y",
            line_code="$MTY13",
            line_description="Rear-Wheel Drive",
            contract_type="PCP",
            monthly_rental_nlp=330.83,
            monthly_rental_glp=397.0,
            currency=Currency.UK,
            market=Market.UK,
            term_of_agreement=48,
        ),
        FinanceLineItem(
            recorded_at="2024-08-20",
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model Y",
            model_code="$MTY13",
            model_description="Model Y",
            line_code="$MTY13",
            line_description="Rear-Wheel Drive",
            contract_type="PCP",
            monthly_rental_nlp=330.83,
            monthly_rental_glp=397.0,
            currency=Currency.UK,
            market=Market.UK,
            term_of_agreement=48,
        ),
        FinanceLineItem(
            recorded_at="2024-08-20",
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model Y",
            model_code="$MTY13",
            model_description="Model Y",
            line_code="$MTY13",
            line_description="Rear-Wheel Drive",
            contract_type="PCP",
            monthly_rental_nlp=330.83,
            monthly_rental_glp=397.0,
            currency=Currency.UK,
            market=Market.UK,
            term_of_agreement=48,
        ),
        FinanceLineItem(
            recorded_at="2024-08-20",
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model Y",
            model_code="$MTY13",
            model_description="Model Y",
            line_code="$MTY13",
            line_description="Rear-Wheel Drive",
            contract_type="PCP",
            monthly_rental_nlp=330.83,
            monthly_rental_glp=397.0,
            currency=Currency.UK,
            market=Market.UK,
            term_of_agreement=48,
        ),
        FinanceLineItem(
            recorded_at="2024-08-20",
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model Y",
            model_code="$MTY13",
            model_description="Model Y",
            line_code="$MTY13",
            line_description="Performance AWD",
            contract_type="PCP",
            monthly_rental_nlp=330.83,
            monthly_rental_glp=397.0,
            currency=Currency.UK,
            market=Market.UK,
            term_of_agreement=48,
        ),
        FinanceLineItem(
            recorded_at="2024-08-20",
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model 3",
            model_code="$MTY13",
            model_description="Model 3",
            line_code="$MTY13",
            line_description="Rear-Wheel Drive",
            contract_type="PCP",
            monthly_rental_nlp=330.83,
            monthly_rental_glp=397.0,
            currency=Currency.UK,
            market=Market.UK,
            term_of_agreement=48,
        ),
        FinanceLineItem(
            recorded_at="2024-08-20",
            vendor=Vendor.TESLA,
            series="my",
            model_range_code="$MDLY",
            model_range_description="Model Y",
            model_code="$MTY13",
            model_description="Model Y",
            line_code="$MTY13",
            line_description="Rear-Wheel Drive",
            contract_type="PCP",
            monthly_rental_nlp=330.83,
            monthly_rental_glp=397.0,
            currency=Currency.UK,
            market=Market.UK,
            term_of_agreement=48,
        ),
    ]

    try:
        config = {
            "output": {
                "directory": TEST_DATA_DIR,
                "finance_options_filename": FILE_NAME,
                "file_type": "dual",
            },
            "scraper": {"enabled": {"audi": ["UK"]}},
        }
        repository = FileSystemFinanceLineItemRepository(config=config)
        repository._save_avro(TEST_DATA_DIR, items)
    except Exception as e:
        pytest.fail(f"_save_avro raised an exception: {e}")
