import json
from pathlib import Path
from src.price_monitor.model.difference_item import DifferenceItem
from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.option_price_difference_item import (
    OptionPriceDifferenceItem,
)
from src.price_monitor.utils.io import (
    get_avro_schema,
    get_csv_headers,
    get_date_from_dir_name,
    get_timestamp_from_dir_name,
)


def test_get_avro_schema_for_line_item():
    with open(Path(__file__).parent / "schemas" / "LineItem.json", "r") as file:
        expected_avro_schema = json.load(file)
        parsed_avro_schema = get_avro_schema(LineItem)

        assert parsed_avro_schema == expected_avro_schema


def test_get_avro_schema_for_difference_item():
    with open(Path(__file__).parent / "schemas" / "DifferenceItem.json", "r") as file:
        expected_avro_schema = json.load(file)
        parsed_avro_schema = get_avro_schema(DifferenceItem)
        assert parsed_avro_schema == expected_avro_schema


def test_get_avro_schema_for_finance_line_item():
    with open(Path(__file__).parent / "schemas" / "FinanceLineItem.json", "r") as file:
        expected_avro_schema = json.load(file)
        parsed_avro_schema = get_avro_schema(FinanceLineItem)

        assert parsed_avro_schema == expected_avro_schema


def test_get_csv_headers_for_line_item():
    expected_csv_headers = [
        "recorded_at",
        "vendor",
        "series",
        "model_range_code",
        "model_range_description",
        "model_code",
        "model_description",
        "line_code",
        "line_description",
        "line_option_codes",
        "currency",
        "net_list_price",
        "gross_list_price",
        "on_the_road_price",
        "market",
        "engine_performance_kw",
        "engine_performance_hp",
        "last_scraped_on",
        "is_current",
    ]

    parsed_csv_headers = get_csv_headers(LineItem)

    assert expected_csv_headers == parsed_csv_headers


def test_get_csv_headers_for_difference_item():
    expected_csv_headers = [
        "recorded_at",
        "vendor",
        "series",
        "model_range_code",
        "model_range_description",
        "model_code",
        "model_description",
        "line_code",
        "line_description",
        "old_value",
        "new_value",
        "reason",
        "market",
    ]

    parsed_csv_headers = get_csv_headers(DifferenceItem)

    assert expected_csv_headers == parsed_csv_headers


def test_get_date_from_dir_name():
    expected_date = "2023-02-22"

    parsed_date = get_date_from_dir_name("/output_dir/date=2023-02-22")

    assert expected_date == parsed_date


def test_get_timestamp_from_dir_name():
    expected_timestamp = "2023-02-22 00:00:00 UTC"

    parsed_date = get_timestamp_from_dir_name("/output_dir/date=2023-02-22")

    assert expected_timestamp == parsed_date


def test_get_avro_schema_for_option_price_difference_item():
    with open(
        Path(__file__).parent / "schemas" / "OptionPriceDifferenceItem.json", "r"
    ) as file:
        expected_avro_schema = json.load(file)
        parsed_avro_schema = get_avro_schema(OptionPriceDifferenceItem)

        assert parsed_avro_schema == expected_avro_schema
