import json
from pathlib import Path
from test.price_monitor.utils.test_data_builder import assert_line_items_list

import pytest

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import (
    LineItemOptionCode,
    create_default_line_item_option_code,
)
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.bmw.parser import (
    adjust_line_options,
    parse_api_token,
    parse_configuration_state,
    parse_constructible_extra_options_for_line,
    parse_effect_date,
    parse_extra_available_options,
    parse_is_volt_48,
    parse_ix_model_codes,
    parse_lines_string,
    parse_model_matrix_to_line_items,
    parse_options_price,
    parse_packages_price,
    parse_tax_date,
)
from src.price_monitor.price_scraper.constants import (
    MISSING_LINE_OPTION_DETAILS,
    NOT_AVAILABLE,
)
from src.price_monitor.utils.clock import today_dashed_str

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"
VENDOR = Vendor.BMW


def test_parse_z_series_model_matrix_to_line_items():
    market = Market.DE
    expected_models_line_items = [
        LineItem(
            recorded_at=today_dashed_str(),
            vendor=VENDOR,
            series="Z",
            model_range_code="G29",
            model_range_description="BMW Z4",
            model_code="HF51",
            model_description="BMW Z4 M40i - automatic",
            line_code="M_PERFORMANCE_LINE",
            line_description="M_PERFORMANCE_LINE",
            line_option_codes=[
                LineItemOptionCode(
                    code="S06C4",
                    description="N/A",
                    type="N/A",
                    included=True,
                    net_list_price=0,
                    gross_list_price=0,
                )
            ],
            currency="EUR",
            market=market,
            net_list_price=56218.49,
            gross_list_price=66900.0,
            engine_performance_kw="250 kW",
            engine_performance_hp="340 hp",
        ),
        LineItem(
            recorded_at=today_dashed_str(),
            vendor=VENDOR,
            series="Z",
            model_range_code="G29",
            model_range_description="BMW Z4",
            model_code="HF11",
            model_description="BMW Z4 sDrive20i",
            line_code="BASIC_LINE",
            line_description="BASIC_LINE",
            line_option_codes=[
                LineItemOptionCode(
                    code="FMASW",
                    description="N/A",
                    type="N/A",
                    included=True,
                    net_list_price=0,
                    gross_list_price=0,
                )
            ],
            currency="EUR",
            market=market,
            net_list_price=40756.30,
            gross_list_price=48500.0,
            engine_performance_kw="145 kW",
            engine_performance_hp="197 hp",
        ),
    ]

    with open(f"{TEST_DATA_DIR}/model_matrix_series_z.json", "r") as file:
        parsed_model_matrix = parse_model_matrix_to_line_items(
            model_matrix=json.load(file), market=market
        )

    assert_line_items_list(expected_models_line_items, parsed_model_matrix)


def test_parse_1_series_model_7k31_line_item():
    market = Market.AT
    option_code_bmw_118i_7k31: list[str] = [
        "S05A1",
        "S06C4",
        "S01DZ",
        "S07E8",
        "S03MF",
        "S0508",
        "S07M9",
        "S0754",
        "S04P2",
        "S0710",
        "S03MQ",
        "S0711",
        "S05AC",
        "S0879",
        "S0715",
        "S08WL",
        "S08KA",
        "S0230",
        "S0552",
        "S04NE",
        "S02VB",
        "S02VC",
        "S08R9",
        "S06AK",
        "S033B",
        "S0544",
        "S0302",
        "S0423",
        "S03M2",
        "S0428",
        "S0704",
        "S05DA",
        "S01DF",
        "FLCRS",
        "S0775",
        "S0654",
        "S06AE",
        "S06AF",
        "S0493",
        "S0494",
        "S01CB",
        "S0851",
        "S05AQ",
        "S08TF",
        "S04GQ",
        "P0300",
        "S02PA",
        "S0249",
        "S01FP",
        "S0760",
        "S0563",
        "S06U3",
    ]
    expected_line_items = [
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="1",
            model_range_code="F40",
            model_range_description="BMW 1er",
            model_code="7K31",
            model_description="BMW 118i - manual",
            line_code="S07E8",
            line_description="Edition ColorVision",
            line_option_codes=[
                create_default_line_item_option_code(code)
                for code in option_code_bmw_118i_7k31
            ],
            currency="EUR",
            net_list_price=35674.92,
            gross_list_price=42809.9,
            on_the_road_price=42809.9,
            market=market,
            engine_performance_kw="100 kW",
            engine_performance_hp="136 hp",
        )
    ]

    with open(f"{TEST_DATA_DIR}/model_matrix_series_1_model_7K31.json", "r") as file:
        parsed_model_matrix = parse_model_matrix_to_line_items(
            model_matrix=json.load(file), market=market
        )
        for item in parsed_model_matrix:
            assert item in expected_line_items
            assert (
                item.asdict()
                == expected_line_items[expected_line_items.index(item)].asdict()
            )


def test_adjust_line_options():
    parsed_options = [
        LineItemOptionCode(
            code="FMASW",
            description="test option 2",
            type="test option",
            net_list_price=0,
            gross_list_price=0,
            included=True,
        ),
        LineItemOptionCode(
            code="P0300",
            description="test option 4",
            type="test option",
            net_list_price=0,
            gross_list_price=0,
            included=False,
        ),
        LineItemOptionCode(
            code="S01CB",
            description="test option 3",
            type="test option",
            net_list_price=0,
            gross_list_price=0,
            included=False,
        ),
        LineItemOptionCode(
            code="S01CD",
            description="test option 4",
            type="test option",
            net_list_price=0,
            gross_list_price=0,
            included=False,
        ),
    ]

    available_options = {
        "option1": {
            "phrases": {"longDescription": "test option 1"},
            "optionType": "test option",
        },
        "FMASW": {
            "phrases": {"longDescription": "test option 2"},
            "optionType": "test option",
        },
        "S01CB": {
            "phrases": {"longDescription": "test option 3"},
            "optionType": "test option",
        },
        "S01CD": {
            "phrases": {"longDescription": "test option 4"},
            "optionType": "test option",
        },
    }

    options_price = {
        "P0300": 100,
        "FMASW": 800,
        "S01CB": 1300,
        "S01CD": -50,
    }

    expected_line_options = [
        LineItemOptionCode(
            code="FMASW",
            description="test option 2",
            type="test option",
            net_list_price=672.27,
            gross_list_price=800,
            included=True,
        ),
        LineItemOptionCode(
            code="S01CB",
            type="test option",
            description="test option 3",
            net_list_price=1092.44,
            gross_list_price=1300,
            included=False,
        ),
    ]

    for item in adjust_line_options(
        Market.DE, parsed_options, available_options, options_price, "BASIC_LINE"
    ):
        assert item in expected_line_options
        assert (
            item.asdict()
            == expected_line_options[expected_line_options.index(item)].asdict()
        )


def test_parse_api_token():
    invalid_html_content_no_script = """
    <html>
        <head></head>
        <body>
        </body>
    </html>
    """
    invalid_html_content_no_base64 = """
    <html>
        <head></head>
        <body>
            <script>
                var conApp = {};
                conApp.inputSettings = "invalid_base64_string";
            </script>
        </body>
    </html>
    """

    # Test invalid inputs
    with pytest.raises(
        ValueError, match="Script tag containing 'conApp.inputSettings' not found"
    ):
        parse_api_token(invalid_html_content_no_script)

    with pytest.raises(ValueError, match="Base64 encoded JSON string not found"):
        parse_api_token(invalid_html_content_no_base64)


def test_parse_tax_date():
    expected_tax_date = "2022-12-15"

    with open(f"{TEST_DATA_DIR}/model_matrix_series_1_model_7K31.json") as file:
        assert (
            parse_tax_date(
                model_matrix=json.load(file),
                series="1",
                model_range_code="F40",
                model_code="7K31",
            )
            == expected_tax_date
        )


def test_parse_effect_date():
    expected_effect_date = "2022-12-15"

    with open(f"{TEST_DATA_DIR}/model_matrix_series_1_model_7K31.json") as file:
        assert (
            parse_effect_date(
                model_matrix=json.load(file),
                series="1",
                model_range_code="F40",
                model_code="7K31",
            )
            == expected_effect_date
        )


def test_parse_is_volt_48():
    expected_is_volt_48 = False

    with open(f"{TEST_DATA_DIR}/configuration_state_details.json") as file:
        parsed_is_volt_48 = parse_is_volt_48(json.load(file))
        assert expected_is_volt_48 == parsed_is_volt_48


def test_parse_options_price():
    expected_options_price = {
        "FEGAT": 0.0,
        "FHLSW": 0.0,
        "FKFIX": 0.0,
        "FKFL1": 300.0,
        "FKKSW": 0.0,
        "FLCEF": 0.0,
        "FLCRS": 0.0,
        "FPDFM": 1700.0,
        "FPDMY": 1700.0,
        "FPDN4": 1400.0,
        "FPDSW": 1700.0,
        "P0300": 0.0,
        "P0475": 0.0,
        "P0668": 0.0,
        "P0A75": 0.0,
        "P0A96": 730.0,
        "P0C1D": 0.0,
        "P0C1G": 730.0,
        "P0C1M": 730.0,
        "P0C1X": 730.0,
        "P0C3N": 760.0,
        "P0C4W": 0.0,
        "P0C5A": 1490.0,
        "S01AG": 50.0,
        "S01FP": 0.0,
        "S01L2": 1420.0,
        "S01N4": 0.0,
        "S01RG": 0.0,
        "S01RL": 0.0,
        "S01RR": 590.0,
        "S01TK": 0.0,
        "S01UP": 1010.0,
        "S01Y2": 500.0,
        "S0205": 2100.0,
        "S0223": 150.0,
        "S0225": 0.0,
        "S0235": 850.0,
        "S0240": 0.0,
        "S0248": 190.0,
        "S0249": 0.0,
        "S0255": 120.0,
        "S025R": 510.0,
        "S026M": 0.0,
        "S02NH": 650.0,
        "S02PA": 0.0,
        "S02TB": 2250.0,
        "S02VB": 0.0,
        "S02VC": 50.0,
        "S02VE": 250.0,
        "S0302": 500.0,
        "S0313": 250.0,
        "S0316": 450.0,
        "S0320": 0.0,
        "S0322": 550.0,
        "S033B": 0.0,
        "S03BE": 0.0,
        "S03DZ": 0.0,
        "S03M2": 0.0,
        "S03MB": 0.0,
        "S03MF": 0.0,
        "S0402": 1180.0,
        "S0413": 200.0,
        "S0420": 350.0,
        "S0423": 0.0,
        "S0428": 0.0,
        "S0430": 500.0,
        "S0431": 170.0,
        "S0441": 60.0,
        "S0450": 50.0,
        "S0459": 850.0,
        "S045A": 680.0,
        "S0465": 200.0,
        "S0470": 50.0,
        "S0481": 500.0,
        "S0488": 250.0,
        "S0493": 0.0,
        "S0494": 0.0,
        "S04GN": 0.0,
        "S04GQ": 0.0,
        "S04P2": 0.0,
        "S04P3": 0.0,
        "S0508": 0.0,
        "S0534": 550.0,
        "S0544": 0.0,
        "S0552": 0.0,
        "S0563": 0.0,
        "S05A1": 0.0,
        "S05A2": 0.0,
        "S05AC": 0.0,
        "S05AQ": 0.0,
        "S05AS": 750.0,
        "S05DA": 0.0,
        "S05DF": 450.0,
        "S05DM": 350.0,
        "S0610": 950.0,
        "S0654": 0.0,
        "S0676": 350.0,
        "S0688": 850.0,
        "S06AE": 0.0,
        "S06AF": 0.0,
        "S06AK": 0.0,
        "S06C1": 0.0,
        "S06C4": 0.0,
        "S06NS": 0.0,
        "S06NW": 400.0,
        "S06U3": 0.0,
        "S06U8": 350.0,
        "S06WD": 0.0,
        "S0704": 0.0,
        "S0710": 0.0,
        "S0711": 0.0,
        "S0715": 0.0,
        "S0754": 0.0,
        "S0760": 0.0,
        "S0775": 0.0,
        "S07D7": 1011.5,
        "S07DA": 1130.5,
        "S07DB": 2808.4,
        "S07E8": 9600.0,
        "S07EV": 1600.0,
        "S07EW": 3000.0,
        "S07LC": 1550.0,
        "S07LD": 3850.0,
        "S07LF": 5450.0,
        "S07LG": 700.0,
        "S07LH": 2450.0,
        "S07LK": 1600.0,
        "S07M9": 0.0,
        "S07NG": 773.5,
        "S07NH": 1237.6,
        "S07NK": 1844.5,
        "S07NM": 1618.4,
        "S07NW": 892.5,
        "S07US": 416.5,
        "S08KA": 0.0,
        "S08KB": 0.0,
        "S08TF": 0.0,
    }
    with open(f"{TEST_DATA_DIR}/options_price_content.json") as file:
        assert expected_options_price == parse_options_price(
            price_details=json.load(file),
        )


def test_parse_packages_price():
    expected_packages_price = {
        "S033B": 2600.0,
        "S07E8": 9600.0,
        "S07EV": 2800.0,
        "S07EW": 4200.0,
        "S07LC": 1550.0,
        "S07LD": 3850.0,
        "S07LF": 5450.0,
        "S07LG": 1000.0,
        "S07LH": 2900.0,
        "S07LK": 2150.0,
    }
    with open(f"{TEST_DATA_DIR}/packages_price_content.json") as file:
        assert expected_packages_price == parse_packages_price(
            price_details=json.load(file),
        )


def test_parse_lines_string():
    expected_lines_str = "BASIC_LINE,M_PERFORMANCE_LINE"
    market = Market.DE
    line_item = LineItem(
        recorded_at=today_dashed_str(),
        vendor=VENDOR,
        series="Z",
        model_range_code="G29",
        model_range_description="BMW Z4",
        model_code="HF11",
        model_description="BMW Z4 sDrive20i - manual",
        line_code="S0337",
        line_description="M Sportpaket",
        line_option_codes=[
            LineItemOptionCode(
                code="S0337",
                description="Test Description",
                type="Test Type",
                net_list_price=84,
                gross_list_price=100,
                included=True,
            )
        ],
        currency="EUR",
        market=market,
        net_list_price=0.00,
        gross_list_price=51400.0,
    )
    with open(f"{TEST_DATA_DIR}/model_matrix_series_z.json") as file:
        lines_str = parse_lines_string(
            model_matrix=json.load(file),
            line_item=line_item,
        )
        assert lines_str == expected_lines_str


def test_parse_extra_available_options():
    expected_possible_available_options = "FHLSW,P0475,S01FP,S02TF,S03BE,S04GN"
    included_options = ["FEGAT", "P0300"]
    lines_str = "BASIC_LINE,M_PERFORMANCE_LINE,S0337,S033B"
    with open(f"{TEST_DATA_DIR}/model_options_details.json") as file:
        parsed_possible_available_options = parse_extra_available_options(
            json.load(file), included_options, lines_str
        )
        assert parsed_possible_available_options == expected_possible_available_options


def test_parse_constructible_extra_options_for_line():
    expected_constructible_options = [
        LineItemOptionCode(
            code="FKFL1",
            description=MISSING_LINE_OPTION_DETAILS,
            type=MISSING_LINE_OPTION_DETAILS,
            net_list_price=0,
            gross_list_price=0,
            included=False,
        ),
        LineItemOptionCode(
            code="FPDFM",
            description=MISSING_LINE_OPTION_DETAILS,
            type=MISSING_LINE_OPTION_DETAILS,
            net_list_price=0,
            gross_list_price=0,
            included=False,
        ),
        LineItemOptionCode(
            code="FPDMY",
            description=MISSING_LINE_OPTION_DETAILS,
            type=MISSING_LINE_OPTION_DETAILS,
            net_list_price=0,
            gross_list_price=0,
            included=False,
        ),
        LineItemOptionCode(
            code="FPDSW",
            description=MISSING_LINE_OPTION_DETAILS,
            type=MISSING_LINE_OPTION_DETAILS,
            net_list_price=0,
            gross_list_price=0,
            included=False,
        ),
    ]
    with open(f"{TEST_DATA_DIR}/options_constructability_details.json") as file:
        parsed_constructible_options = parse_constructible_extra_options_for_line(
            constructability_status=json.load(file)
        )
        for option in parsed_constructible_options:
            assert option in expected_constructible_options
            assert (
                option.asdict()
                == expected_constructible_options[
                    expected_constructible_options.index(option)
                ].asdict()
            )


def test_parse_configuration_state():
    expected_configuration_state = "ddd74851-baa9-4dfd-aeb4-97e30424a7d7"

    with open(f"{TEST_DATA_DIR}/configuration_state_details.json") as file:
        parsed_configuration_state = parse_configuration_state(json.load(file))
        assert expected_configuration_state == parsed_configuration_state


def test_new_line_characters_remove_from_option_description():
    available_options = {
        "option1": {
            "phrases": {"longDescription": "test option 1"},
            "optionType": "test option",
        },
        "FMASW": {
            "phrases": {"longDescription": "test option 2"},
            "optionType": "test option",
        },
        "S01CB": {
            "phrases": {"longDescription": "test option 3"},
            "optionType": "test option",
        },
        "S01CD": {
            "phrases": {"longDescription": "test option 4"},
            "optionType": "test option",
        },
    }

    options_price = {
        "P0300": 100,
        "FMASW": 800,
        "S01CB": 1300,
        "S01CD": -50,
    }

    parsed_options = [
        LineItemOptionCode(
            code="FMASW",
            description="test option \n2",
            type="test option",
            net_list_price=0,
            gross_list_price=0,
            included=True,
        ),
        LineItemOptionCode(
            code="P0300",
            description="test option \n4",
            type="test option",
            net_list_price=0,
            gross_list_price=0,
            included=False,
        ),
        LineItemOptionCode(
            code="S01CB",
            description="test option \n3",
            type="test option",
            net_list_price=0,
            gross_list_price=0,
            included=False,
        ),
        LineItemOptionCode(
            code="S01CD",
            description="test option \n4",
            type="test option",
            net_list_price=0,
            gross_list_price=0,
            included=False,
        ),
    ]
    adjusted_line_options = adjust_line_options(
        Market.DE, parsed_options, available_options, options_price, "BASIC_LINE"
    )
    for line_option in adjusted_line_options:
        assert "\n" not in line_option.description


def test_adjust_line_options_when_option_type_is_model_variant_or_line_then_they_should_be_appended_to_the_list_for_basic_line():
    parsed_options = [
        LineItemOptionCode(
            code="S01CB",
            description="test option 3",
            type="modelVariant",
            net_list_price=89,
            gross_list_price=100,
            included=True,
        ),
        LineItemOptionCode(
            code="S01CD",
            description="test option 4",
            type="line",
            net_list_price=43,
            gross_list_price=50,
            included=True,
        ),
    ]

    available_options = {
        "S01CB": {
            "phrases": {"longDescription": "test option 3"},
            "optionType": "modelVariant",
        },
        "S01CD": {
            "phrases": {"longDescription": "test option 4"},
            "optionType": "line",
        },
    }

    options_price = {
        "S01CB": 100,
        "S01CD": 50,
    }

    expected_line_options = [
        LineItemOptionCode(
            code="S01CB",
            type="modelVariant",
            description="test option 3",
            net_list_price=84.03,
            gross_list_price=100,
            included=False,
        ),
        LineItemOptionCode(
            code="S01CD",
            type="line",
            description="test option 4",
            net_list_price=42.02,
            gross_list_price=50,
            included=False,
        ),
    ]

    actual_line_options = adjust_line_options(
        Market.DE, parsed_options, available_options, options_price, "BASIC_LINE"
    )
    assert actual_line_options == expected_line_options


def test_adjust_line_options_when_option_type_is_model_variant_or_line_then_they_should_not_be_appended_to_the_list_except_for_basic_line():
    parsed_options = [
        LineItemOptionCode(
            code="S01CB",
            description="test option 3",
            type="modelVariant",
            net_list_price=89,
            gross_list_price=100,
            included=True,
        ),
        LineItemOptionCode(
            code="S01CD",
            description="test option 4",
            type="line",
            net_list_price=43,
            gross_list_price=50,
            included=True,
        ),
        LineItemOptionCode(
            code="S01CF",
            description="test option 4",
            type="paint",
            net_list_price=43,
            gross_list_price=50,
            included=True,
        ),
    ]

    available_options = {
        "S01CB": {
            "phrases": {"longDescription": "test option 3"},
            "optionType": "modelVariant",
        },
        "S01CD": {
            "phrases": {"longDescription": "test option 4"},
            "optionType": "line",
        },
        "S01CF": {
            "phrases": {"longDescription": "test option 4"},
            "optionType": "paint",
        },
    }

    options_price = {
        "S01CB": 100,
        "S01CD": 50,
        "S01CF": 50,
    }

    expected_line_options = [
        LineItemOptionCode(
            code="S01CF",
            description="test option 4",
            type="paint",
            net_list_price=42.02,
            gross_list_price=50,
            included=True,
        )
    ]

    actual_line_options = adjust_line_options(
        Market.DE, parsed_options, available_options, options_price, "Sports"
    )
    assert actual_line_options == expected_line_options


def test_engine_performance_when_target_value_is_absent_then_return_na():
    market = Market.DE
    expected_models_line_items = [
        LineItem(
            recorded_at=today_dashed_str(),
            vendor=VENDOR,
            series="Z",
            model_range_code="G29",
            model_range_description="BMW Z4",
            model_code="HF51",
            model_description="BMW Z4 M40i - automatic",
            line_code="M_PERFORMANCE_LINE",
            line_description="M_PERFORMANCE_LINE",
            line_option_codes=[
                LineItemOptionCode(
                    code="S06C4",
                    description="N/A",
                    type="N/A",
                    included=True,
                    net_list_price=0,
                    gross_list_price=0,
                )
            ],
            currency="EUR",
            market=market,
            net_list_price=56218.49,
            gross_list_price=66900.0,
            on_the_road_price=66900.0,
            engine_performance_kw=NOT_AVAILABLE,
            engine_performance_hp="340 hp",
        ),
        LineItem(
            recorded_at=today_dashed_str(),
            vendor=VENDOR,
            series="Z",
            model_range_code="G29",
            model_range_description="BMW Z4",
            model_code="HF11",
            model_description="BMW Z4 sDrive20i",
            line_code="BASIC_LINE",
            line_description="BASIC_LINE",
            line_option_codes=[
                LineItemOptionCode(
                    code="FMASW",
                    description="N/A",
                    type="N/A",
                    included=True,
                    net_list_price=0,
                    gross_list_price=0,
                )
            ],
            currency="EUR",
            market=market,
            net_list_price=40756.30,
            gross_list_price=48500.0,
            on_the_road_price=48500.0,
            engine_performance_kw="145 kW",
            engine_performance_hp=NOT_AVAILABLE,
        ),
    ]

    with open(
        f"{TEST_DATA_DIR}/model_matrix_series_z_without_target_variable.json", "r"
    ) as file:
        parsed_model_matrix = parse_model_matrix_to_line_items(
            model_matrix=json.load(file), market=market
        )

    assert_line_items_list(expected_models_line_items, parsed_model_matrix)


def test_parse_ix_model_codes():
    expected_ix_model_codes = ["IXMA", "IXMB", "IXMC", "IXSA"]
    with open(f"{TEST_DATA_DIR}/ix_model_matrix.json", "r") as file:
        parsed_ix_model_codes = parse_ix_model_codes(model_matrix=json.load(file))

    assert expected_ix_model_codes == parsed_ix_model_codes
