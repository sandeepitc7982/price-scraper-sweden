import json
from pathlib import Path
from test.price_monitor.utils.test_data_builder import create_test_line_item

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.audi.parser import (
    parse_available_model_links,
    parse_line_item_options_for_trimline,
    parse_model_line_item,
    parse_options_type,
    replace_options_type,
)
from src.price_monitor.utils.clock import today_dashed_str
from src.price_monitor.utils.line_item_factory import create_line_item_option_code

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"
VENDOR = Vendor.AUDI


def test_parse_available_model_links_when_price_is_present_it_should_return_in_first_list():
    expected_links_having_price = [
        "/de/brand/de/neuwagen/e-tron-gt/audi-e-tron-gt",
        "/de/brand/de/neuwagen/e-tron-gt/audi-rs-e-tron-gt",
        "/de/brand/de/neuwagen/q8-e-tron/q8-e-tron",
        "/de/brand/de/neuwagen/q8-e-tron/q8-sportback-e-tron",
        "/de/brand/de/neuwagen/q8-e-tron/sq8-e-tron",
        "/de/brand/de/neuwagen/q8-e-tron/sq8-sportback-e-tron",
        "/de/brand/de/neuwagen/a1/a1-sportback",
        "/de/brand/de/neuwagen/a3/a3-sportback",
        "/de/brand/de/neuwagen/a3/a3-sportback-tfsi-e",
        "/de/brand/de/neuwagen/a3/a3-limousine",
        "/de/brand/de/neuwagen/a3/s3-sportback",
        "/de/brand/de/neuwagen/a3/s3-limousine",
        "/de/brand/de/neuwagen/a4/a4-limousine",
        "/de/brand/de/neuwagen/a4/a4-avant",
        "/de/brand/de/neuwagen/a4/a4-allroad-quattro",
        "/de/brand/de/neuwagen/a4/rs-4-avant",
        "/de/brand/de/neuwagen/a5/a5-coupe",
        "/de/brand/de/neuwagen/a5/a5-sportback",
        "/de/brand/de/neuwagen/a5/a5-cabriolet",
        "/de/brand/de/neuwagen/a5/s5-cabriolet",
        "/de/brand/de/neuwagen/a5/rs-5-coupe",
        "/de/brand/de/neuwagen/a5/rs-5-sportback",
        "/de/brand/de/neuwagen/a6/a6-limousine",
        "/de/brand/de/neuwagen/a6/a6-limousine-tfsi-e",
        "/de/brand/de/neuwagen/a6/a6-avant",
        "/de/brand/de/neuwagen/a6/a6-avant-tfsi-e",
        "/de/brand/de/neuwagen/a6/a6-allroad-quattro",
        "/de/brand/de/neuwagen/a6/s6-limousine",
        "/de/brand/de/neuwagen/a6/s6-avant",
        "/de/brand/de/neuwagen/a7/a7-sportback",
        "/de/brand/de/neuwagen/a7/a7-sportback-tfsi-e",
        "/de/brand/de/neuwagen/a7/s7-sportback",
        "/de/brand/de/neuwagen/a8/a8",
        "/de/brand/de/neuwagen/a8/a8-tfsi-e",
        "/de/brand/de/neuwagen/a8/a8-l",
        "/de/brand/de/neuwagen/a8/a8-l-tfsi-e",
        "/de/brand/de/neuwagen/a8/s8",
        "/de/brand/de/neuwagen/q2/q2",
        "/de/brand/de/neuwagen/q2/sq2",
        "/de/brand/de/neuwagen/q3/q3",
        "/de/brand/de/neuwagen/q3/q3-tfsi-e",
        "/de/brand/de/neuwagen/q3/q3-sportback",
        "/de/brand/de/neuwagen/q3/q3-sportback-tfsi-e",
        "/de/brand/de/neuwagen/q4-e-tron/q4-e-tron",
        "/de/brand/de/neuwagen/q4-e-tron/q4-e-tron-sportback",
        "/de/brand/de/neuwagen/q5/q5",
        "/de/brand/de/neuwagen/q5/q5-tfsi-e",
        "/de/brand/de/neuwagen/q5/q5-sportback",
        "/de/brand/de/neuwagen/q5/q5-sportback-tfsi-e",
        "/de/brand/de/neuwagen/q8/q8-suv",
        "/de/brand/de/neuwagen/q8/sq8-suv",
        "/de/brand/de/neuwagen/r8/r8-coupe-v10-performance-quattro",
        "/de/brand/de/neuwagen/r8/r8-coupe-v10-performance-rwd",
    ]

    with open(f"{TEST_DATA_DIR}/model_list_de.html", "r") as file:
        links_having_price, link_not_having_price = parse_available_model_links(file)

        assert expected_links_having_price == links_having_price


def test_parse_available_model_links_when_price_is_not_present_it_should_return_in_second_list():
    expected_link_not_having_price = [
        "/de/brand/de/neuwagen/a1/a1-allstre",
        "/de/brand/de/neuwagen/a3/a3-sportback-g-tron",
        "/de/brand/de/neuwagen/a3/rs-3-sportback",
        "/de/brand/de/neuwagen/a3/rs-3-limousine",
        "/de/brand/de/neuwagen/a4/s4-limousine",
        "/de/brand/de/neuwagen/a4/s4-avant",
        "/de/brand/de/neuwagen/a5/s5-coupe",
        "/de/brand/de/neuwagen/a5/s5-sportback",
        "/de/brand/de/neuwagen/a6/rs-6-avant",
        "/de/brand/de/neuwagen/a6/rs-6-avant-performance",
        "/de/brand/de/neuwagen/a7/rs-7-sportback",
        "/de/brand/de/neuwagen/a7/rs-7-sportback-performance",
        "/de/brand/de/neuwagen/q3/rs-q3",
        "/de/brand/de/neuwagen/q3/rs-q3-sportback",
        "/de/brand/de/neuwagen/q5/sq5",
        "/de/brand/de/neuwagen/q5/sq5-sportback",
        "/de/brand/de/neuwagen/q7/q7",
        "/de/brand/de/neuwagen/q7/q7-tfsi-e",
        "/de/brand/de/neuwagen/q7/sq7",
        "/de/brand/de/neuwagen/q8/rs-q8",
        "/de/brand/de/neuwagen/tt/tt-coupe",
        "/de/brand/de/neuwagen/tt/tt-roadster",
        "/de/brand/de/neuwagen/tt/tts-coupe",
        "/de/brand/de/neuwagen/tt/tts-roadster",
        "/de/brand/de/neuwagen/tt/tt-rs-coupe",
        "/de/brand/de/neuwagen/tt/tt-rs-roadster",
        "/de/brand/de/neuwagen/r8/r8-spyder-v10-performance-quattro",
        "/de/brand/de/neuwagen/r8/r8-spyder-v10-performance-rwd",
        "/de/brand/de/neuwagen/r8/r8-gt",
    ]

    with open(f"{TEST_DATA_DIR}/model_list_de.html", "r") as file:
        links_having_price, link_not_having_price = parse_available_model_links(file)

        assert expected_link_not_having_price == link_not_having_price


def test_parse_model_line_items_for_a8():
    expected_line_item = create_test_line_item(
        recorded_at=today_dashed_str(),
        last_scraped_on=today_dashed_str(),
        vendor=VENDOR,
        series="a8",
        model_range_code="a8",
        model_range_description="A8",
        model_code="a8",
        model_description="50 TDI quattro tiptronic",
        line_code="4NC04A0EB3_2023",
        line_description="DEFAULT",
        line_option_codes=[],
        currency="EUR",
        net_list_price=83949.58,
        gross_list_price=99900.0,
        on_the_road_price=69605.0,
        market=Market.DE,
    )

    with open(f"{TEST_DATA_DIR}/a8_trimline_default.json", "r") as file:
        assert (
            parse_model_line_item(
                model_link="/de/brand/de/neuwagen/a8/a8",
                model_code="a8",
                model_configuration=json.loads(file.read()),
                market=Market.DE,
            ).asdict()
            == expected_line_item.asdict()
        )


def test_parse_options_type():
    expected_options_details = {
        "70T": "Lade-Equipment",
        "73A": "Lade-Equipment",
        "73J": "Lade-Equipment",
        "KH5": "Komfort",
        "4F2": "Komfort",
        "4I3": "Komfort",
        "7UG": "Infotainment",
    }

    with open(f"{TEST_DATA_DIR}/options_type.json", "r") as file:
        for code, type in parse_options_type(json.loads(file.read())).items():
            assert code in expected_options_details
            assert type == expected_options_details[code]


def test_parse_line_item_options_for_trimline():
    expected_line_options = [
        create_line_item_option_code(
            code="0E0E",
            description="Mythosschwarz Metallic",
            type="exteriorColor",
            included=False,
            net_list_price=882.35,
            gross_list_price=1050.0,
        ),
        create_line_item_option_code(
            code="0N1",
            description="Ohne Allradlenkung",
            type="equipment",
            included=True,
            net_list_price=0.0,
            gross_list_price=0,
        ),
        create_line_item_option_code(
            code="1BK",
            description="adaptive air suspension",
            type="equipment",
            included=False,
            net_list_price=1260.5,
            gross_list_price=1500.0,
        ),
        create_line_item_option_code(
            code="trimline_default",
            description="Basis",
            type="trimline",
            included=True,
            net_list_price=0.0,
            gross_list_price=0,
        ),
    ]

    with open(f"{TEST_DATA_DIR}/etron_configuration_details.json", "r") as file:
        trimline_details = json.loads(file.read())
    option_common_details_file = open(
        f"{TEST_DATA_DIR}/etron_option_common_details.json", "r"
    )
    option_common_details = json.loads(option_common_details_file.read())["items"]
    for option in parse_line_item_options_for_trimline(
        trimline_details,
        option_common_details,
        Market.DE,
    ):
        assert option in expected_line_options
        assert (
            option.asdict()
            == expected_line_options[expected_line_options.index(option)].asdict()
        )
        assert "\n" not in option.description


def test_replace_options_type_updates_option_type_when_option_code_is_found():
    line_option_codes = [
        create_line_item_option_code(
            code="0E0E",
            description="Mythosschwarz Metallic",
            type="exteriorColor",
            included=False,
            net_list_price=882.35,
            gross_list_price=1050.0,
        ),
        create_line_item_option_code(
            code="0N1",
            description="Ohne Allradlenkung",
            type="equipment",
            included=True,
            net_list_price=0.0,
            gross_list_price=0,
        ),
    ]
    option_types = {
        "0E0E": "Lade-Equipment",
        "KH5": "Komfort",
        "0N1": "Komfort",
    }
    replace_options_type(line_option_codes, option_types)
    for option in line_option_codes:
        assert option.type == option_types[option.code]


def test_replace_options_type_does_not_update_option_type_when_option_code_not_found():
    line_option_codes = [
        create_line_item_option_code(
            code="0N1",
            description="Ohne Allradlenkung",
            type="equipment",
            included=True,
            net_list_price=0.0,
            gross_list_price=0,
        ),
    ]
    option_types = {
        "0E0E": "Lade-Equipment",
        "KH5": "Komfort",
    }
    replace_options_type(line_option_codes, option_types)
    assert line_option_codes[0].type == "equipment"


def test_replace_options_type_when_option_price_is_0_and_option_in_common_option_type_then_option_should_be_included():
    line_option_codes = [
        create_line_item_option_code(
            code="0N1",
            description="Ohne Allradlenkung",
            type="Exterior Colors",
            included=False,
            net_list_price=0.0,
            gross_list_price=0,
        ),
    ]
    option_types = {
        "0E0E": "Lade-Equipment",
        "KH5": "Komfort",
    }
    replace_options_type(line_option_codes, option_types)
    assert line_option_codes[0].included is True


def test_replace_options_type_when_option_price_is_not_0_and_option_in_common_option_type_then_option_should_be_excluded():
    line_option_codes = [
        create_line_item_option_code(
            code="0N1",
            description="Ohne Allradlenkung",
            type="Exterior Colors",
            included=False,
            net_list_price=0.0,
            gross_list_price=10,
        ),
    ]
    option_types = {
        "0E0E": "Lade-Equipment",
        "KH5": "Komfort",
    }
    replace_options_type(line_option_codes, option_types)
    assert line_option_codes[0].included is False
