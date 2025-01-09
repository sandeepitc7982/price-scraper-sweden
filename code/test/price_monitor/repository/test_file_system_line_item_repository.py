import glob
import os
from pathlib import Path
from test.price_monitor.builder.line_item_builder import LineItemBuilder
from assertpy import assert_that
import pytest

from src.price_monitor.model.line_item_option_code import (
    create_default_line_item_option_code,
)
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.utils.clock import (
    today_dashed_str_with_key,
    yesterday_dashed_str_with_key,
)

TEST_DATA_DIR = f"{Path(__file__).parent}/data"
FILE_NAME = "test_prices"
ITEMS = [
    LineItemBuilder().with_vendor(Vendor.AUDI).with_gross_list_price(45110).build(),
    LineItemBuilder()
    .with_vendor(Vendor.BMW)
    .with_gross_list_price(88870)
    .with_market(Market.NL)
    .build(),
    LineItemBuilder()
    .with_vendor(Vendor.BMW)
    .with_net_list_price(84538)
    .with_gross_list_price(101445)
    .with_market(Market.AT)
    .build(),
    LineItemBuilder()
    .with_vendor(Vendor.MERCEDES_BENZ)
    .with_model_range_description("B-KLASSE SPORTS TOURER")
    .with_net_list_price(55662)
    .with_gross_list_price(66237)
    .with_market(Market.DE)
    .build(),
    LineItemBuilder()
    .with_vendor(Vendor.AUDI)
    .with_market(Market.DE)
    .with_series("a6")
    .with_model_code("a6limo")
    .with_line_code("trimline_sport")
    .with_line_option_code([create_default_line_item_option_code("0E0E")])
    .with_net_list_price(45798.32)
    .with_gross_list_price(54500)
    .build(),
    LineItemBuilder()
    .with_vendor(Vendor.TESLA)
    .with_market(Market.DE)
    .with_series("mx")
    .with_net_list_price(45798.32)
    .with_gross_list_price(54500)
    .build(),
    LineItemBuilder()
    .with_vendor(Vendor.AUDI)
    .with_market(Market.DE)
    .with_series("e-tron-gt")
    .with_model_range_code("suv")
    .with_net_list_price(45798.32)
    .with_gross_list_price(54500)
    .build(),
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
            "prices_filename": FILE_NAME,
            "file_type": "avro",
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load(date=today_dashed_str_with_key()) == ITEMS


def test_save_and_load_csv():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
            "file_type": "csv",
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load(date=today_dashed_str_with_key()) == ITEMS


def test_save_csv_and_load_avro():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
            "file_type": "csv",
        }
    }
    repository = FileSystemLineItemRepository(config=config)
    repository.save(ITEMS, date=today_dashed_str_with_key())

    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
            "file_type": "avro",
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    assert repository.load(date=today_dashed_str_with_key()) == ITEMS


def test_save_avro_and_load_csv():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
            "file_type": "avro",
        }
    }
    repository = FileSystemLineItemRepository(config=config)
    repository.save(ITEMS, date=today_dashed_str_with_key())

    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
            "file_type": "csv",
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    assert repository.load(date=today_dashed_str_with_key()) == ITEMS


def test_load_market():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load_market(
        date=today_dashed_str_with_key(), vendor=Vendor.BMW, market=Market.AT
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.BMW)
        .with_net_list_price(84538)
        .with_gross_list_price(101445)
        .with_market(Market.AT)
        .build()
    ]


def test_load_market_for_yesterday():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)
    repository.save(ITEMS, date=yesterday_dashed_str_with_key())
    yesterday_line_items = repository.load_market(
        date=yesterday_dashed_str_with_key(), vendor=Vendor.BMW, market=Market.AT
    )
    expected_line_item = (
        LineItemBuilder()
        .with_vendor(Vendor.BMW)
        .with_net_list_price(84538)
        .with_gross_list_price(101445)
        .with_market(Market.AT)
        .build()
    )
    assert_that(yesterday_line_items).contains_only(expected_line_item)


def test_load_model_filter_by_model_range_description():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load_model_filter_by_model_range_description(
        date=today_dashed_str_with_key(),
        vendor=Vendor.MERCEDES_BENZ,
        market=Market.DE,
        model_range_description="B-KLASSE SPORTS TOURER",
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.MERCEDES_BENZ)
        .with_model_range_description("B-KLASSE SPORTS TOURER")
        .with_net_list_price(55662)
        .with_gross_list_price(66237)
        .with_market(Market.DE)
        .build(),
    ]


def test_load_model_filter_by_model_range_description_for_yesterday():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=yesterday_dashed_str_with_key())

    assert repository.load_model_filter_by_model_range_description(
        date=yesterday_dashed_str_with_key(),
        vendor=Vendor.MERCEDES_BENZ,
        market=Market.DE,
        model_range_description="B-KLASSE SPORTS TOURER",
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.MERCEDES_BENZ)
        .with_model_range_description("B-KLASSE SPORTS TOURER")
        .with_net_list_price(55662)
        .with_gross_list_price(66237)
        .with_market(Market.DE)
        .build(),
    ]


def test_load_model_filter_by_model_range_code():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load_model_filter_by_model_range_code(
        date=today_dashed_str_with_key(),
        vendor=Vendor.AUDI,
        market=Market.DE,
        series="e-tron-gt",
        model_range_code="suv",
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_series("e-tron-gt")
        .with_model_range_code("suv")
        .with_market(Market.DE)
        .build(),
    ]


def test_load_model_filter_by_model_range_code_for_yesterday():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=yesterday_dashed_str_with_key())

    assert repository.load_model_filter_by_model_range_code(
        date=yesterday_dashed_str_with_key(),
        vendor=Vendor.AUDI,
        market=Market.DE,
        series="e-tron-gt",
        model_range_code="suv",
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_series("e-tron-gt")
        .with_model_range_code("suv")
        .with_market(Market.DE)
        .build(),
    ]


def test_load_model_filter_by_series():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load_model_filter_by_series(
        date=today_dashed_str_with_key(),
        vendor=Vendor.TESLA,
        market=Market.DE,
        series="mx",
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.TESLA)
        .with_market(Market.DE)
        .with_series("mx")
        .with_net_list_price(45798.32)
        .with_gross_list_price(54500)
        .build(),
    ]


def test_load_model_filter_by_series_for_yesterday():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=yesterday_dashed_str_with_key())

    assert repository.load_model_filter_by_series(
        date=yesterday_dashed_str_with_key(),
        vendor=Vendor.TESLA,
        market=Market.DE,
        series="mx",
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.TESLA)
        .with_market(Market.DE)
        .with_series("mx")
        .with_net_list_price(45798.32)
        .with_gross_list_price(54500)
        .build(),
    ]


def test_load_line_option_codes_for_line_code_that_exists_in_yesterdays_data():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=yesterday_dashed_str_with_key())

    assert repository.load_line_option_codes_for_line_code(
        date=yesterday_dashed_str_with_key(),
        market=Market.DE,
        vendor=Vendor.AUDI,
        series="a6",
        model_code="a6limo",
        line_code="trimline_sport",
    ) == [create_default_line_item_option_code("0E0E")]


def test_load_line_option_codes_for_line_code_that_does_not_exist_in_yesterdays_data():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=yesterday_dashed_str_with_key())

    assert (
        repository.load_line_option_codes_for_line_code(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
            model_code="a10limo",
            line_code="trimlin_sport",
            series="a10",
        )
        == []
    )


def test_load_line_option_codes_for_line_code_that_exists_in_todays_data():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load_line_option_codes_for_line_code(
        date=today_dashed_str_with_key(),
        market=Market.DE,
        vendor=Vendor.AUDI,
        series="a6",
        model_code="a6limo",
        line_code="trimline_sport",
    ) == [create_default_line_item_option_code("0E0E")]


def test_load_line_option_codes_for_line_code_that_does_not_exist_in_todays_data():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert (
        repository.load_line_option_codes_for_line_code(
            date=today_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
            model_code="a10limo",
            line_code="trimlin_sport",
            series="a10",
        )
        == []
    )


def test_load_model_filter_by_line_code():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load_model_filter_by_line_code(
        date=today_dashed_str_with_key(),
        market=Market.DE,
        vendor=Vendor.AUDI,
        line_code="trimline_sport",
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_market(Market.DE)
        .with_series("a6")
        .with_model_code("a6limo")
        .with_line_code("trimline_sport")
        .with_line_option_code([create_default_line_item_option_code("0E0E")])
        .with_net_list_price(45798.32)
        .with_gross_list_price(54500)
        .build(),
    ]


def test_load_model_filter_by_line_code_for_yesterday():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=yesterday_dashed_str_with_key())

    assert repository.load_model_filter_by_line_code(
        date=yesterday_dashed_str_with_key(),
        market=Market.DE,
        vendor=Vendor.AUDI,
        line_code="trimline_sport",
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_market(Market.DE)
        .with_series("a6")
        .with_model_code("a6limo")
        .with_line_code("trimline_sport")
        .with_line_option_code([create_default_line_item_option_code("0E0E")])
        .with_net_list_price(45798.32)
        .with_gross_list_price(54500)
        .build(),
    ]


def test_load_model_filter_by_model_code():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load_model_filter_by_model_code(
        date=today_dashed_str_with_key(),
        market=Market.DE,
        vendor=Vendor.AUDI,
        model_code="a6limo",
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_market(Market.DE)
        .with_series("a6")
        .with_model_code("a6limo")
        .with_line_code("trimline_sport")
        .with_line_option_code([create_default_line_item_option_code("0E0E")])
        .with_net_list_price(45798.32)
        .with_gross_list_price(54500)
        .build(),
    ]


def test_load_model_filter_by_model_code_for_yesterday():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=yesterday_dashed_str_with_key())

    assert repository.load_model_filter_by_model_code(
        date=yesterday_dashed_str_with_key(),
        market=Market.DE,
        vendor=Vendor.AUDI,
        model_code="a6limo",
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_market(Market.DE)
        .with_series("a6")
        .with_model_code("a6limo")
        .with_line_code("trimline_sport")
        .with_line_option_code([create_default_line_item_option_code("0E0E")])
        .with_net_list_price(45798.32)
        .with_gross_list_price(54500)
        .build(),
    ]


def test_load_model_filter_by_model_code_returns_empty_list_when_no_matches():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save([], date=today_dashed_str_with_key())

    assert (
        repository.load_model_filter_by_model_code(
            date=today_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
            model_code="a6limo",
        )
        == []
    )


def test_load_model_filter_by_trim_line():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=today_dashed_str_with_key())

    assert repository.load_model_filter_by_trim_line(
        date=today_dashed_str_with_key(),
        market=Market.DE,
        vendor=Vendor.AUDI,
        model_code="a6limo",
        line_code="trimline_sport",
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_market(Market.DE)
        .with_series("a6")
        .with_model_code("a6limo")
        .with_line_code("trimline_sport")
        .with_line_option_code([create_default_line_item_option_code("0E0E")])
        .with_net_list_price(45798.32)
        .with_gross_list_price(54500)
        .build(),
    ]


def test_load_model_filter_by_trim_line_for_yesterday():
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
        }
    }
    repository = FileSystemLineItemRepository(config=config)

    repository.save(ITEMS, date=yesterday_dashed_str_with_key())

    assert repository.load_model_filter_by_trim_line(
        date=yesterday_dashed_str_with_key(),
        market=Market.DE,
        vendor=Vendor.AUDI,
        model_code="a6limo",
        line_code="trimline_sport",
    ) == [
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_market(Market.DE)
        .with_series("a6")
        .with_model_code("a6limo")
        .with_line_code("trimline_sport")
        .with_line_option_code([create_default_line_item_option_code("0E0E")])
        .with_net_list_price(45798.32)
        .with_gross_list_price(54500)
        .build(),
    ]


def test_return_empty_list_for_no_file():
    repository = FileSystemLineItemRepository(
        config={
            "output": {
                "directory": TEST_DATA_DIR,
                "prices_filename": "not_a_real_file",
            }
        }
    )

    assert repository.load(date="19990909") == []


def test_update_line_items_when_data_is_already_present_for_scraped_data_then_data_should_be_replaced():
    expected_line_items = [
        LineItemBuilder()
        .with_vendor(Vendor.BMW)
        .with_net_list_price(500)
        .with_market(Market.NL)
        .build(),
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_market(Market.DE)
        .with_net_list_price(10)
        .build(),
    ]
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
            "file_type": "avro",
        },
        "scraper": {"enabled": {"audi": ["DE"]}},
    }
    existing_line_items = [
        LineItemBuilder()
        .with_vendor(Vendor.BMW)
        .with_net_list_price(500)
        .with_market(Market.NL)
        .build(),
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_market(Market.DE)
        .with_net_list_price(100)
        .build(),
    ]
    new_line_items = [
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_market(Market.DE)
        .with_net_list_price(100)
        .build()
    ]
    line_item_repository = FileSystemLineItemRepository(config=config)

    line_item_repository.update_line_items(existing_line_items, new_line_items, config)
    actual_line_items = line_item_repository.load(date=today_dashed_str_with_key())

    assert actual_line_items == expected_line_items


def test_update_line_items_when_data_is_not_present_for_that_market_then_data_should_be_appended():
    expected_line_items = [
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_market(Market.DE)
        .with_net_list_price(100)
        .build(),
        LineItemBuilder()
        .with_vendor(Vendor.BMW)
        .with_net_list_price(500)
        .with_market(Market.DE)
        .build(),
    ]
    config = {
        "output": {
            "directory": TEST_DATA_DIR,
            "prices_filename": FILE_NAME,
            "file_type": "avro",
        },
        "scraper": {"enabled": {"bmw": ["DE"]}},
    }
    existing_line_items = [
        LineItemBuilder()
        .with_vendor(Vendor.AUDI)
        .with_market(Market.DE)
        .with_net_list_price(100)
        .build()
    ]
    new_line_items = [
        LineItemBuilder()
        .with_vendor(Vendor.BMW)
        .with_net_list_price(500)
        .with_market(Market.DE)
        .build()
    ]
    line_item_repository = FileSystemLineItemRepository(config=config)

    line_item_repository.update_line_items(existing_line_items, new_line_items, config)
    actual_line_items = line_item_repository.load(date=today_dashed_str_with_key())

    assert expected_line_items == actual_line_items
