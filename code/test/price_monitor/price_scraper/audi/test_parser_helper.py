import json
from pathlib import Path
from unittest.mock import patch

from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import LineItem
from src.price_monitor.price_scraper.audi.parser_helper import (
    get_engine_performance,
    parse_engine_performance_kw_and_hp,
    parse_line_option_codes,
    parse_model_line_item,
)
from src.price_monitor.price_scraper.constants import (
    MISSING_LINE_OPTION_DETAILS,
    NOT_AVAILABLE,
)
from src.price_monitor.utils.clock import today_dashed_str

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"
VENDOR = Vendor.AUDI


def test_parse_model_line_item_for_us():
    expected_line_item = LineItem(
        recorded_at=today_dashed_str(),
        last_scraped_on=today_dashed_str(),
        vendor=Vendor.AUDI,
        series="e-tron-gt",
        model_range_code="suv",
        model_range_description="Audi  Q8  e-tron®",
        model_code="GEGCVC0S0DWD9WPT_2024",
        model_description="quattro®",
        line_code="default",
        line_description="DEFAULT",
        line_option_codes=[],
        currency="USD",
        net_list_price=87550.0,
        gross_list_price=0.0,
        market=Market.US,
        engine_performance_kw="85",
        engine_performance_hp="123",
    )

    with open(f"{TEST_DATA_DIR}/us_model_configuration.json", "r") as file:
        model_details = json.loads(file.read())
        assert (
            parse_model_line_item(
                model_details,
                "/de/brand/de/neuwagen/e-tron-gt/suv/audi-e-tron-gt",
                Market.US,
                {
                    "GEGCVC0S0DWD9WPT_2024": {
                        "max-output-ps": "123",
                        "max-output-kw": "85",
                        "max-output": "",
                    }
                },
            ).asdict()
            == expected_line_item.asdict()
        )


def test_parse_model_line_item_for_uk():
    expected_line_item = LineItem(
        recorded_at=today_dashed_str(),
        last_scraped_on=today_dashed_str(),
        vendor=Vendor.AUDI,
        series="etrongt",
        model_range_code="audi-e-tron-gt",
        model_range_description="e-tron GT quattro",
        model_code="F83RJ70WB4_2024",
        model_description="e-tron GT quattro 60 quattro",
        line_code="default",
        line_description="DEFAULT",
        line_option_codes=[],
        currency="GBP",
        net_list_price=72154.17,
        gross_list_price=86585.0,
        on_the_road_price=87415.0,
        market=Market.UK,
        engine_performance_kw="123",
    )
    with open(f"{TEST_DATA_DIR}/uk_model_configuration.json", "r") as file:
        model_details = json.loads(file.read())
        assert (
            parse_model_line_item(
                model_details,
                "etrongt/audi-e-tron-gt",
                Market.UK,
                {"F83RJ70WB4_2024": {"max-output-kw": "123", "max-output": ""}},
            ).asdict()
            == expected_line_item.asdict()
        )


def test_parse_line_option_codes_for_us():
    expected_line_option_codes = [
        LineItemOptionCode(
            code="0E0E",
            description="Mythos Black metallic",
            type="extcolor",
            included=False,
            net_list_price=595.0,
            gross_list_price=595.0,
        ),
        LineItemOptionCode(
            code="1BK",
            description=MISSING_LINE_OPTION_DETAILS,
            type="Exterior",
            included=True,
            net_list_price=0,
            gross_list_price=0,
        ),
        LineItemOptionCode(
            code="1D6",
            description="Trailer hitch",
            type="Exterior",
            included=False,
            net_list_price=750.0,
            gross_list_price=750.0,
        ),
        LineItemOptionCode(
            code="2Y2Y",
            description="Glacier White metallic",
            type="extcolor",
            included=False,
            net_list_price=595.0,
            gross_list_price=595.0,
        ),
        LineItemOptionCode(
            code="WPR",
            description="AC charging package",
            type="Exterior",
            included=False,
            net_list_price=1850,
            gross_list_price=1850.0,
        ),
    ]

    with open(f"{TEST_DATA_DIR}/us_model_configuration.json", "r") as file:
        model_details = json.loads(file.read())
        car_info = json.loads(
            open(f"{TEST_DATA_DIR}/us_options_description.json", "r").read()
        )
        descriptions = car_info["items"]
        option_types = car_info["families"]
        parsed_line_option_codes = parse_line_option_codes(
            model_details, descriptions, option_types, Market.US
        )
        for parsed_option, expected_option in zip(
            parsed_line_option_codes, expected_line_option_codes
        ):
            assert parsed_option.asdict() == expected_option.asdict()


def test_parse_line_option_codes_for_uk():
    expected_line_option_codes = [
        LineItemOptionCode(
            code="0E0E",
            description="Mythos Black metallic",
            type="extcolor",
            included=False,
            net_list_price=495.83,
            gross_list_price=595.0,
        ),
        LineItemOptionCode(
            code="1BK",
            description=MISSING_LINE_OPTION_DETAILS,
            type="Exterior",
            included=True,
            net_list_price=0,
            gross_list_price=0,
        ),
        LineItemOptionCode(
            code="1D6",
            description="Trailer hitch",
            type="Exterior",
            included=False,
            net_list_price=625,
            gross_list_price=750.0,
        ),
        LineItemOptionCode(
            code="2Y2Y",
            description="Glacier White metallic",
            type="extcolor",
            included=False,
            net_list_price=495.83,
            gross_list_price=595.0,
        ),
        LineItemOptionCode(
            code="WPR",
            description="AC charging package",
            type="Exterior",
            included=False,
            net_list_price=1541.67,
            gross_list_price=1850.0,
        ),
    ]

    with open(f"{TEST_DATA_DIR}/us_model_configuration.json", "r") as file:
        model_details = json.loads(file.read())
        car_info = json.loads(
            open(f"{TEST_DATA_DIR}/us_options_description.json", "r").read()
        )
        descriptions = car_info["items"]
        option_types = car_info["families"]
        parsed_line_option_codes = parse_line_option_codes(
            model_details, descriptions, option_types, Market.UK
        )
        for parsed_option, expected_option in zip(
            parsed_line_option_codes, expected_line_option_codes
        ):
            assert parsed_option.asdict() == expected_option.asdict()


def test_parse_engine_performance_kw_and_hp_when_different_patterns_pass_then_return_kw_hp_list():
    expected_ep = [
        ["110", "150"],
        ["110", "150"],
        ["110", "150"],
        ["110", "150"],
        ["110", "150"],
        ["110", "150"],
        ["110", "150"],
        ["110", "NA"],
        ["110", "150"],
        ["110", "150"],
        ["120", "163"],
        ["120", "163"],
        ["140", "190"],
        ["142", "193"],
        ["150", "204"],
        ["150", "204"],
        ["150", "204"],
        ["150", "204"],
        ["150", "204"],
        ["150", NOT_AVAILABLE],
        ["150", "204"],
        ["170", "231"],
        ["170", "231"],
        ["180", "245"],
        ["180", "245"],
        ["180", "245"],
        ["195", "265"],
        ["195", "265"],
        ["195", "265"],
        ["195", "265"],
        ["195", NOT_AVAILABLE],
        ["150", "204"],
        ["150", "204"],
        ["150", "204"],
        ["210", "286"],
        ["210", "286"],
        ["210", NOT_AVAILABLE],
        ["210", "286"],
        ["210", "286"],
        ["220", "299"],
        ["220", NOT_AVAILABLE],
        ["221", "300"],
        ["221", NOT_AVAILABLE],
        ["225", "306"],
        ["245", "333"],
        ["250", "340"],
        ["250", "340"],
        ["250", "340"],
        ["251", "341"],
        ["253", "344"],
        ["195", "265"],
        ["195", "265"],
        ["285", "388"],
        ["290", "394"],
        ["290", "394"],
        ["220", "299"],
        ["300", "408"],
        ["331", "450"],
        ["331", "450"],
        ["331", "450"],
        ["340", "462"],
        ["253", "344"],
        ["360", "490"],
        ["373", "507"],
        ["390", "476"],
        ["419", NOT_AVAILABLE],
        ["420", "571"],
        ["441", "600"],
        ["456", "620"],
        ["463", "630"],
        ["475", "598"],
        ["70", "95"],
        ["85", "116"],
        ["85", "116"],
        ["85", "116"],
        ["360", "490"],
        ["NA", "NA"],
    ]
    actual_ep = []
    with open(f"{TEST_DATA_DIR}/engine_performance.txt") as file:
        while True:
            line = file.readline()
            actual_ep.append(parse_engine_performance_kw_and_hp(line))
            if not line:
                break
    assert expected_ep == actual_ep


@patch(
    "src.price_monitor.price_scraper.audi.parser_helper.parse_engine_performance_kw_and_hp"
)
def test_get_engine_performance_when_max_output_kw_not_present(
    mock_parse_engine_performance_kw_and_hp,
):
    expected_engine_performance = ("110", "123")
    mock_parse_engine_performance_kw_and_hp.return_value = ["110", NOT_AVAILABLE]
    model_details = {
        "F83RJ70WB4_2024": {
            "max-output-ps": "123",
            "max-output": "110 kW 4,000 - 6,000 1/min",
        }
    }
    actual_engine_performance = get_engine_performance("F83RJ70WB4_2024", model_details)
    assert expected_engine_performance == actual_engine_performance


@patch(
    "src.price_monitor.price_scraper.audi.parser_helper.parse_engine_performance_kw_and_hp"
)
def test_get_engine_performance_when_max_output_ps_not_present(
    mock_parse_engine_performance_kw_and_hp,
):
    expected_engine_performance = ("123", NOT_AVAILABLE)
    mock_parse_engine_performance_kw_and_hp.return_value = ["110", NOT_AVAILABLE]
    model_details = {
        "F83RJ70WB4_2024": {
            "max-output-kw": "123",
            "max-output": "110 kW 4,000 - 6,000 1/min",
        }
    }
    actual_engine_performance = get_engine_performance("F83RJ70WB4_2024", model_details)
    assert expected_engine_performance == actual_engine_performance


@patch(
    "src.price_monitor.price_scraper.audi.parser_helper.parse_engine_performance_kw_and_hp"
)
def test_get_engine_performance_when_nothing_is_present(
    mock_parse_engine_performance_kw_and_hp,
):
    expected_engine_performance = (NOT_AVAILABLE, NOT_AVAILABLE)
    mock_parse_engine_performance_kw_and_hp.return_value = [
        NOT_AVAILABLE,
        NOT_AVAILABLE,
    ]
    model_details = {"F83RJ70WB4_2024": {}}
    actual_engine_performance = get_engine_performance("F83RJ70WB4_2024", model_details)
    assert expected_engine_performance == actual_engine_performance
