import json
import unittest
from pathlib import Path
from test.price_monitor.price_scraper.mercedes_benz.data_test_parser import (
    models_data,
    option_code_list,
)
from test.price_monitor.utils.test_data_builder import create_test_line_item

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.parser_usa import (
    AvailableModel,
    AvailableTrimLine,
    MercedesBenzUSAParser,
)
from src.price_monitor.utils.clock import today_dashed_str

TEST_DATA_DIR = f"{Path(__file__).parent}/sample_usa_apis"
VENDOR = Vendor.MERCEDES_BENZ


class TestMercedesBenzUSAParser(unittest.TestCase):
    def test_parse_available_models_returns_empty_if_no_active_models(self):
        models_data_empty = """{"result": {"activeModels": {}}}"""
        parser = MercedesBenzUSAParser()

        actual = parser.parse_available_models(models_data_empty)

        assert actual == []

    def test_parse_available_models_returns_mercedes_benz_usa_model_structure(self):
        parser = MercedesBenzUSAParser()
        expected_models = [
            AvailableModel(
                "C43W4", True, "/en/vehicles/build/c-class/sedan/c43w4/lines"
            ),
            AvailableModel(
                "C300A", False, "/en/vehicles/build/c-class/cabriolet/c300a"
            ),
        ]

        actual = parser.parse_available_models(
            str(json.dumps(models_data)).replace("'", '"')
        )

        assert actual == expected_models

    def test_parse_trim_line(self):
        parser = MercedesBenzUSAParser()
        expected_result = create_test_line_item(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="C-Class",
            model_range_code="C300A",
            model_range_description="C-Class Convertible",
            model_code="205483",
            model_description="C 300 Cabriolet",
            line_code="205483",
            line_description="BASIC LINE",
            line_option_codes=[],
            currency="USD",
            net_list_price=57250.0,
            gross_list_price=0.0,
            market=Market.US,
        )
        with open(f"{TEST_DATA_DIR}/cabriolet_base_model.html", "r") as payload:
            actual_result = parser.parse_trim_line(payload.read(), "BASIC LINE", "")
            assert actual_result == expected_result

    def test_parse_line_codes(self):
        parser = MercedesBenzUSAParser()
        expected_result = [
            AvailableTrimLine(
                line_code="DX0",
                line_description="Premium Trim",
                line_path="/en/vehicles/build/c-class/sedan/c300w/dx0",
            ),
            AvailableTrimLine(
                line_code="DX1",
                line_description="Exclusive Trim",
                line_path="/en/vehicles/build/c-class/sedan/c300w/dx1",
            ),
            AvailableTrimLine(
                line_code="DX2",
                line_description="Pinnacle Trim",
                line_path="/en/vehicles/build/c-class/sedan/c300w/dx2",
            ),
        ]
        with open(f"{TEST_DATA_DIR}/sedan_model.html", "r") as payload:
            assert parser.parse_line_codes(payload.read()) == expected_result

    def test_parse_available_models_returns_empty_list_when_extract_fails(self):
        parser = MercedesBenzUSAParser()
        data = ""
        assert parser.parse_line_codes(data) == []

    def test_parse_option_code_list(self):
        parser = MercedesBenzUSAParser()
        expected_result = option_code_list
        with open(f"{TEST_DATA_DIR}/cabriolet_base_model.html", "r") as payload:
            data = parser._extract_model_json_from_html(payload.read())
        assert parser.parse_option_codes(data["categories"]) == expected_result
