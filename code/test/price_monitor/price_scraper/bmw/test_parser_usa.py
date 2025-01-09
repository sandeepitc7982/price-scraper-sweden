import json
from pathlib import Path
from test.price_monitor.utils.test_data_builder import create_test_line_item

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.bmw.parser_usa import (
    extract_line_item,
    extract_price,
    generate_line_item_options,
    parse_all_available_options,
    parse_extra_designs_list,
    parse_is_option_constructible,
    parse_line_items,
    parse_model_code_list_from_json,
)
from src.price_monitor.utils.clock import today_dashed_str

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"
VENDOR = Vendor.BMW


def test_parse_model_code_list_from_json_for_series_ix():
    expected_model_code_list = {"24II", "24IJ"}

    with open(f"{TEST_DATA_DIR}/us_model_list_content_for_series_iX.json", "r") as file:
        parsed_model_code_list = parse_model_code_list_from_json(
            model_list_json=json.load(file)
        )
        assert expected_model_code_list == parsed_model_code_list


def test_parse_model_code_list_from_json_for_series_2():
    expected_model_code_list = {
        "232B",
        "232J",
        "232V",
        "232K",
        "232T",
        "232R",
        "232U",
        "232C",
    }

    with open(f"{TEST_DATA_DIR}/us_model_list_content_for_series_2.json", "r") as file:
        parsed_model_code_list = parse_model_code_list_from_json(
            model_list_json=json.load(file)
        )
        assert expected_model_code_list == parsed_model_code_list


def test_parse_line_items_when_design_list_is_not_empty_then_return_line_items_for_each_design():
    expected_line_items = [
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=Vendor.BMW,
            series="iX",
            model_range_code="I20",
            model_range_description="Sports Activity Vehicle",
            model_code="24II",
            model_description="iX xDrive50",
            line_code="S0ZBM",
            line_description="BMW i Signature Blue Package",
            line_option_codes=[],
            currency="USD",
            net_list_price=87100.0,
            gross_list_price=0.00,
            market=Market.US,
        ),
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=Vendor.BMW,
            series="iX",
            model_range_code="I20",
            model_range_description="Sports Activity Vehicle",
            model_code="24II",
            model_description="iX xDrive50",
            line_code="S0ZSP",
            line_description="Sport",
            line_option_codes=[],
            currency="USD",
            net_list_price=87100.0,
            gross_list_price=0.00,
            market=Market.US,
        ),
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=Vendor.BMW,
            series="iX",
            model_range_code="I20",
            model_range_description="Sports Activity Vehicle",
            model_code="24II",
            model_description="iX xDrive50",
            line_code="S0Z12",
            line_description="Shadowline",
            line_option_codes=[],
            currency="USD",
            net_list_price=87100.0,
            gross_list_price=0.00,
            market=Market.US,
        ),
    ]
    with open(f"{TEST_DATA_DIR}/us_line_details_content.json", "r") as file:
        parsed_line_items = parse_line_items(json.load(file))
        for item in parsed_line_items:
            assert item in expected_line_items
            assert (
                item.asdict()
                == expected_line_items[expected_line_items.index(item)].asdict()
            )


def test_parse_line_items_when_design_list_is_empty_then_return_basic_line_item():
    expected_line_item = LineItem(
        recorded_at=today_dashed_str(),
        last_scraped_on=today_dashed_str(),
        vendor=Vendor.BMW,
        series="iX",
        model_range_code="I20",
        model_range_description="Sports Activity Vehicle",
        model_code="24II",
        model_description="iX xDrive50",
        line_code="BASIC_LINE",
        line_description="BASIC_LINE",
        line_option_codes=[],
        currency="USD",
        net_list_price=87100.0,
        gross_list_price=0.00,
        market=Market.US,
    )
    with open(f"{TEST_DATA_DIR}/us_line_details_content.json", "r") as file:
        model_details = json.load(file)
        model_details["configuration"]["designs"] = []
        parsed_line_item = parse_line_items(model_details)
        assert parsed_line_item[0].asdict() == expected_line_item.asdict()


def test_extract_line_item():
    expected_line_item = create_test_line_item(
        recorded_at=today_dashed_str(),
        last_scraped_on=today_dashed_str(),
        vendor=Vendor.BMW,
        series="iX",
        model_range_code="I20",
        model_range_description="Sports Activity Vehicle",
        model_code="24II",
        model_description="iX xDrive50",
        line_code="FZTPK",
        line_description="M Sport",
        line_option_codes=[],
        currency="USD",
        net_list_price=87100.0,
        gross_list_price=0.00,
        market=Market.US,
    )
    with open(f"{TEST_DATA_DIR}/us_line_details_content.json", "r") as file:
        parsed_line_item = extract_line_item(json.load(file), "FZTPK", "M Sport")
        assert expected_line_item.asdict() == parsed_line_item.asdict()


def test_generate_line_item_options():
    expected_line_item_options = [
        LineItemOptionCode(
            code="P0300",
            description="Alpine White",
            type="colors",
            included=True,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="P0475",
            description="Black Sapphire Metallic",
            type="colors",
            included=False,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="P0A90",
            description="Dark Graphite Metallic",
            type="colors",
            included=False,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="P0A96",
            description="Mineral White Metallic",
            type="colors",
            included=False,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="P0C1M",
            description="Phytonic Blue Metallic",
            type="colors",
            included=False,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="P0C35",
            description="Blue Ridge Mountain Metallic",
            type="colors",
            included=False,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="P0C3N",
            description="Storm Bay Metallic",
            type="colors",
            included=False,
            net_list_price=1950.0,
            gross_list_price=1950.0,
        ),
        LineItemOptionCode(
            code="P0C4A",
            description="Oxide Grey metallic",
            type="colors",
            included=False,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="P0C57",
            description="Aventurin Red Metallic",
            type="colors",
            included=False,
            net_list_price=1950.0,
            gross_list_price=1950.0,
        ),
    ]
    options_list = [
        {
            "code": "P0300",
            "isSelected": True,
            "isIncluded": False,
            "isRecommended": True,
            "selectedPackageContent": [],
            "price": 0.0,
            "isPotentialConflicts": False,
        },
        {
            "code": "P0475",
            "isSelected": False,
            "isIncluded": False,
            "isRecommended": False,
            "selectedPackageContent": [],
            "price": 0.0,
            "isPotentialConflicts": False,
        },
        {
            "code": "P0A90",
            "isSelected": False,
            "isIncluded": False,
            "isRecommended": False,
            "selectedPackageContent": [],
            "price": 0.0,
            "isPotentialConflicts": False,
        },
        {
            "code": "P0A96",
            "isSelected": False,
            "isIncluded": False,
            "isRecommended": False,
            "selectedPackageContent": [],
            "price": 0.0,
            "isPotentialConflicts": True,
        },
        {
            "code": "P0C1M",
            "isSelected": False,
            "isIncluded": False,
            "isRecommended": False,
            "selectedPackageContent": [],
            "price": 0.0,
            "isPotentialConflicts": False,
        },
        {
            "code": "P0C35",
            "isSelected": False,
            "isIncluded": False,
            "isRecommended": False,
            "selectedPackageContent": [],
            "price": 0.0,
            "isPotentialConflicts": False,
        },
        {
            "code": "P0C3N",
            "isSelected": False,
            "isIncluded": False,
            "isRecommended": False,
            "selectedPackageContent": [],
            "price": 1950.0,
            "isPotentialConflicts": True,
        },
        {
            "code": "P0C4A",
            "isSelected": False,
            "isIncluded": False,
            "isRecommended": False,
            "selectedPackageContent": [],
            "price": 0.0,
            "isPotentialConflicts": False,
        },
        {
            "code": "P0C57",
            "isSelected": False,
            "isIncluded": False,
            "isRecommended": False,
            "selectedPackageContent": [],
            "price": 1950.0,
            "isPotentialConflicts": True,
        },
    ]
    option_type = "colors"

    with open(f"{TEST_DATA_DIR}/us_option_details.json", "r") as file:
        generated_line_item_options = generate_line_item_options(
            option_details=json.load(file),
            option_type=option_type,
            options_list=options_list,
        )
        for item in generated_line_item_options:
            assert item in expected_line_item_options
            assert (
                item.asdict()
                == expected_line_item_options[
                    expected_line_item_options.index(item)
                ].asdict()
            )


def test_parse_all_available_options():
    expected_line_item_options = [
        LineItemOptionCode(
            code="ACC_HC_001",
            description="Flexible Fast Charger",
            type="accessories",
            included=True,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="ACC_HC_002",
            description="NEMA 14-50 Adapter",
            type="accessories",
            included=True,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="ACC_HC_003",
            description="BMW Wallbox",
            type="accessories",
            included=False,
            net_list_price=600.0,
            gross_list_price=600.0,
        ),
        LineItemOptionCode(
            code="ACC_HC_004",
            description="Concierge Installation Service by Qmerit",
            type="accessories",
            included=False,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="ACC_PC_001",
            description="2 years of complimentary 30-min charging sessions with Electrify America",
            type="accessories",
            included=True,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="S03L7",
            description="BMW Individual Titanium Bronze Exterior Trim",
            type="options",
            included=False,
            net_list_price=500.0,
            gross_list_price=500.0,
        ),
        LineItemOptionCode(
            code="S0453",
            description="Front ventilated seats",
            type="options",
            included=False,
            net_list_price=500.01,
            gross_list_price=500.01,
        ),
        LineItemOptionCode(
            code="S04FM",
            description="Multi-Functional Seats",
            type="options",
            included=False,
            net_list_price=1600.0,
            gross_list_price=1600.0,
        ),
        LineItemOptionCode(
            code="S04HC",
            description="Radiant Heating Package",
            type="options",
            included=False,
            net_list_price=950.0,
            gross_list_price=950.0,
        ),
        LineItemOptionCode(
            code="S05AZ",
            description="Icon Adaptive LED Headlights with Laserlight",
            type="options",
            included=False,
            net_list_price=1000.0,
            gross_list_price=1000.0,
        ),
        LineItemOptionCode(
            code="S06F1",
            description="Bowers & Wilkins Diamond Surround Sound System",
            type="options",
            included=False,
            net_list_price=3400.0,
            gross_list_price=3400.0,
        ),
        LineItemOptionCode(
            code="S0ZDY",
            description="Driving Assistance Professional Package",
            type="packages",
            included=False,
            net_list_price=2300.0,
            gross_list_price=2300.0,
        ),
        LineItemOptionCode(
            code="S0ZLX",
            description="Luxury Package",
            type="packages",
            included=False,
            net_list_price=1150.0,
            gross_list_price=1150.0,
        ),
        LineItemOptionCode(
            code="S0PKG66",
            description="Titanium Bronze Trim",
            type="trims",
            included=True,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="ACC_BMW_UC",
            description="BMW Ultimate Care+",
            type="vehiclePrograms",
            included=False,
            net_list_price=850.0,
            gross_list_price=850.0,
        ),
        LineItemOptionCode(
            code="ACC_BMW_UCPlus2",
            description="BMW Ultimate Care+ 2 Bundle",
            type="vehiclePrograms",
            included=False,
            net_list_price=2049.0,
            gross_list_price=2049.0,
        ),
        LineItemOptionCode(
            code="ACC_BMW_UCPlus4",
            description="BMW Ultimate Care+ 4 Bundle",
            type="vehiclePrograms",
            included=False,
            net_list_price=2749.0,
            gross_list_price=2749.0,
        ),
    ]

    with open(f"{TEST_DATA_DIR}/us_option_details.json", "r") as option_details_file:
        line_details_file = open(f"{TEST_DATA_DIR}/us_line_details_content.json", "r")
        line_details = json.load(line_details_file)
        parsed_line_item_options = parse_all_available_options(
            line_details=line_details, option_details=json.load(option_details_file)
        )
        for item in parsed_line_item_options:
            assert item in expected_line_item_options
            assert (
                item
                == expected_line_item_options[expected_line_item_options.index(item)]
            )


def test_parse_all_available_options_does_not_scrape_when_option_type_is_designs():
    expected_line_item_options = [
        LineItemOptionCode(
            code="ACC_HC_001",
            description="Flexible Fast Charger",
            type="accessories",
            included=True,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="ACC_HC_002",
            description="NEMA 14-50 Adapter",
            type="accessories",
            included=True,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="ACC_HC_003",
            description="BMW Wallbox",
            type="accessories",
            included=False,
            net_list_price=600.0,
            gross_list_price=600.0,
        ),
        LineItemOptionCode(
            code="ACC_HC_004",
            description="Concierge Installation Service by Qmerit",
            type="accessories",
            included=False,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="ACC_PC_001",
            description="2 years of complimentary 30-min charging sessions with Electrify America",
            type="accessories",
            included=True,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="S03L7",
            description="BMW Individual Titanium Bronze Exterior Trim",
            type="options",
            included=False,
            net_list_price=500.0,
            gross_list_price=500.0,
        ),
        LineItemOptionCode(
            code="S0453",
            description="Front ventilated seats",
            type="options",
            included=False,
            net_list_price=500.01,
            gross_list_price=500.01,
        ),
        LineItemOptionCode(
            code="S04FM",
            description="Multi-Functional Seats",
            type="options",
            included=False,
            net_list_price=1600.0,
            gross_list_price=1600.0,
        ),
        LineItemOptionCode(
            code="S04HC",
            description="Radiant Heating Package",
            type="options",
            included=False,
            net_list_price=950.0,
            gross_list_price=950.0,
        ),
        LineItemOptionCode(
            code="S05AZ",
            description="Icon Adaptive LED Headlights with Laserlight",
            type="options",
            included=False,
            net_list_price=1000.0,
            gross_list_price=1000.0,
        ),
        LineItemOptionCode(
            code="S06F1",
            description="Bowers & Wilkins Diamond Surround Sound System",
            type="options",
            included=False,
            net_list_price=3400.0,
            gross_list_price=3400.0,
        ),
        LineItemOptionCode(
            code="S0ZDY",
            description="Driving Assistance Professional Package",
            type="packages",
            included=False,
            net_list_price=2300.0,
            gross_list_price=2300.0,
        ),
        LineItemOptionCode(
            code="S0ZLX",
            description="Luxury Package",
            type="packages",
            included=False,
            net_list_price=1150.0,
            gross_list_price=1150.0,
        ),
        LineItemOptionCode(
            code="S0PKG66",
            description="Titanium Bronze Trim",
            type="trims",
            included=True,
            net_list_price=0.0,
            gross_list_price=0.0,
        ),
        LineItemOptionCode(
            code="ACC_BMW_UC",
            description="BMW Ultimate Care+",
            type="vehiclePrograms",
            included=False,
            net_list_price=850.0,
            gross_list_price=850.0,
        ),
        LineItemOptionCode(
            code="ACC_BMW_UCPlus2",
            description="BMW Ultimate Care+ 2 Bundle",
            type="vehiclePrograms",
            included=False,
            net_list_price=2049.0,
            gross_list_price=2049.0,
        ),
        LineItemOptionCode(
            code="ACC_BMW_UCPlus4",
            description="BMW Ultimate Care+ 4 Bundle",
            type="vehiclePrograms",
            included=False,
            net_list_price=2749.0,
            gross_list_price=2749.0,
        ),
    ]

    with open(f"{TEST_DATA_DIR}/us_option_details.json", "r") as option_details_file:
        line_details_file = open(f"{TEST_DATA_DIR}/us_line_details_content.json", "r")
        line_details = json.load(line_details_file)
        parsed_line_item_options = parse_all_available_options(
            line_details=line_details, option_details=json.load(option_details_file)
        )
        for item in parsed_line_item_options:
            assert item in expected_line_item_options
            assert (
                item
                == expected_line_item_options[expected_line_item_options.index(item)]
            )


def test_extract_price():
    expected_extracted_price = 87100

    with open(f"{TEST_DATA_DIR}/us_line_details_content.json", "r") as line_details:
        parsed_extracted_price = extract_price(json.load(line_details))
        assert expected_extracted_price == parsed_extracted_price


def test_parse_extra_designs_list():
    expected_extra_designs_list = ["S0ZBM", "S0ZSP"]
    with open(f"{TEST_DATA_DIR}/us_line_details_content.json", "r") as line_details:
        parsed_extra_designs_list = parse_extra_designs_list(json.load(line_details))
        assert expected_extra_designs_list == parsed_extra_designs_list


def test_parse_is_option_constructible():
    extra_designs_list = ["S0ZBM", "S0ZSP"]
    with open(f"{TEST_DATA_DIR}/us_line_details_content.json", "r") as line_details:
        parsed_is_option_constructible = parse_is_option_constructible(
            extra_designs_list, json.load(line_details)
        )
        assert parsed_is_option_constructible is True


def test_new_line_characters_remove_from_option_description():
    options_list = [
        {
            "code": "P0300",
            "isSelected": True,
            "isIncluded": False,
            "isRecommended": True,
            "selectedPackageContent": [],
            "price": 0.0,
            "isPotentialConflicts": False,
        }
    ]
    option_type = "colors"
    with open(f"{TEST_DATA_DIR}/us_option_details.json", "r") as file:
        generated_line_item_options = generate_line_item_options(
            option_details=json.load(file),
            option_type=option_type,
            options_list=options_list,
        )
        for item in generated_line_item_options:
            assert "\n" not in item.description


def test_generated_line_item_options_filters_options_with_word_deletion_in_description():
    option_list = [
        {"code": "S0ZDM", "isSelected": True, "price": 100.0},
        {"code": "B", "isSelected": True, "price": 200.0},
    ]
    option_details = {
        "S0ZDM": {
            "name": "Moonroof deletion",
            "type": "options",
            "included": False,
            "net_list_price": -1000.0,
            "gross_list_price": -1000.0,
            "predicted_category": "",
        },
        "B": {"name": "Moonroof"},
    }
    line_items = generate_line_item_options(
        option_details=option_details, option_type="type", options_list=option_list
    )
    assert line_items == [
        LineItemOptionCode(
            code="B",
            description="Moonroof",
            type="type",
            included=True,
            net_list_price=200.0,
            gross_list_price=200.0,
            predicted_category="",
        )
    ]
