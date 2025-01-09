import json
import unittest
from pathlib import Path
from test.price_monitor.utils.test_data_builder import (
    create_test_line_item,
    create_test_line_item_option_code,
)
from unittest.mock import patch

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import LineItem
from src.price_monitor.price_scraper.constants import NOT_AVAILABLE
from src.price_monitor.price_scraper.mercedes_benz.parser import (
    _append_option_code,
    build_model_range_description,
    get_option_codes,
    parse_available_models_links,
    parse_engine_performance_kw_and_hp,
    parse_line_item,
    parse_line_options,
    parse_trim_line,
    parse_trim_line_codes,
    split_engine_performance,
)
from src.price_monitor.utils.clock import today_dashed_str

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"
VENDOR = Vendor.MERCEDES_BENZ


class TestMBParser(unittest.TestCase):
    def test_parse_available_model_links_when_class_id_available(self):
        expected_model_links = {
            "EQS-KLASSE/LIMOUSINE_LANG",
            "E-KLASSE/COUPE",
            "A-KLASSE/KOMPAKT-LIMOUSINE",
            "G-KLASSE/GELAENDEWAGEN",
            "A-KLASSE/LIMOUSINE",
            "E-KLASSE/T-MODELL",
            "B-KLASSE/SPORTS TOURER",
            "E-KLASSE/CABRIOLET",
            "CLS-KLASSE/COUPE",
            "EQS-KLASSE/OFFROADER",
            "SL-KLASSE/ROADSTER",
            "C-KLASSE/T-MODELL",
            "C-KLASSE/CABRIOLET",
            "E-KLASSE/LIMOUSINE",
            "GLC-KLASSE/OFFROADER",
            "CLA-KLASSE/SHOOTING BRAKE",
            "GLE-KLASSE/OFFROADER",
            "EQB-KLASSE/OFFROADER",
            "GLA-KLASSE/OFFROADER",
            "C-KLASSE/COUPE",
            "EQE-KLASSE/OFFROADER",
            "CLA-KLASSE/COUPE",
            "S-KLASSE/LIMOUSINE_LANG",
            "S-KLASSE/LIMOUSINE",
            "EQE-KLASSE/LIMOUSINE_LANG",
            "GLC-KLASSE/COUPE",
            "GL-KLASSE/OFFROADER",
            "GLB-KLASSE/OFFROADER",
            "C-KLASSE/LIMOUSINE",
            "EQA-KLASSE/OFFROADER",
            "GT-KLASSE/4-TUERER COUPE",
            "GLE-KLASSE/COUPE",
        }

        with open(f"{TEST_DATA_DIR}/MODELS.json") as payload:
            assert (
                parse_available_models_links(json.load(payload)) == expected_model_links
            )

    def test_parse_line_items(self):
        expected_models_line_items = LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="EQB",
            model_range_code="X243",
            model_range_description="EQB Offroader",
            model_code="2436021",
            model_description="EQB 250+",
            line_code="2436021",
            line_description="EQB 250+",
            line_option_codes=[],
            currency="EUR",
            net_list_price=44970.0,
            gross_list_price=53514.3,
            on_the_road_price=53514.3,
            market=Market.DE,
        )
        with open(f"{TEST_DATA_DIR}/EQB_OFFROADER.json", "r") as payload:
            data = json.load(payload)
            vehicle = data["vehicles"][0]
            class_body_names = data["classBodyNames"][0]
            item = parse_line_item(vehicle, class_body_names, Market.DE, "")
            assert item.asdict() == expected_models_line_items.asdict()

    def test_get_option_codes(self):
        expected_option_codes = [
            "PC-PUF",
            "PC-PAZ",
            "PC-P60",
            "LU-799",
            "LU-956",
            "LU-197",
            "LU-922",
            "LU-992",
            "LU-040",
            "LU-149",
            "SA-RWZ",
            "SA-RQW",
            "SA-RWQ",
            "SA-RPF",
            "SA-R01",
            "SA-8R9",
            "SA-652",
            "PC-PAX",
            "SA-U50",
            "SA-597",
            "PC-PAF",
            "SA-550",
            "SA-846",
            "PC-PTF",
            "AU-651",
            "AU-851",
            "AU-859",
            "AU-861",
            "SA-U17",
            "SA-Y05",
            "SA-872",
            "SA-401",
            "SA-H08",
            "SA-51H",
            "SA-H67",
            "SA-H39",
            "SA-H20",
            "SA-H73",
            "SA-697",
            "SA-732",
            "SA-757",
            "SA-775",
            "SA-781",
            "SA-661",
            "SA-L6J",
            "SA-L6K",
            "SA-L6H",
            "SA-443",
            "SA-543",
            "SA-51U",
            "SA-59U",
            "SA-61U",
            "SA-580",
            "PC-P53",
            "SA-581",
            "PC-PSO",
            "PC-PSR",
            "SA-256",
            "SA-865",
            "SA-444",
            "PC-PAG",
            "PC-PBG",
            "SA-553",
            "PC-P47",
            "PC-PBH",
            "SA-682",
            "SA-293",
            "SA-9B6",
            "SA-B30",
            "SA-B80",
            "SA-9B7",
            "SA-U70",
            "SA-B07",
        ]
        with open(f"{TEST_DATA_DIR}/EQE_OFFROADER_OPTIONS.json", "r") as payload:
            data = json.load(payload)
            assert sorted(expected_option_codes) == get_option_codes(
                data["componentCategories"], True
            )

    def test_build_model_range_description_that_has_class_names_with_klasse(self):
        expected_model_range_description = "A-KLASSE OFFROADER"
        model = "A-KLASSE/OFFROADER"

        actual_model_range_description = build_model_range_description(model)

        assert expected_model_range_description == actual_model_range_description

    def test_build_model_range_description_that_has_class_names_without_klasse(self):
        expected_model_range_description = "EQS OFFROADER"
        model = "EQS-KLASSE/OFFROADER"

        actual_model_range_description = build_model_range_description(model)

        assert expected_model_range_description == actual_model_range_description

    def test_build_model_range_description_that_has_body_names_as_limousine_lang(self):
        expected_model_range_description = "S-KLASSE LIMOUSINE LANG"
        model = "S-KLASSE/LIMOUSINE_LANG"

        actual_model_range_description = build_model_range_description(model)

        assert expected_model_range_description == actual_model_range_description

    def test_new_line_characters_remove_from_option_description(self):
        with open(f"{TEST_DATA_DIR}/EQE_OFFROADER_OPTIONS.json", "r") as payload:
            actual_line_options = parse_line_options(
                True, json.load(payload), True, "BASIC_LINE"
            )
            for item in actual_line_options:
                assert "\n" not in item.description

    def test_parse_trim_line_codes(self):
        expected_option_codes = ["PC-P59", "PC-950"]
        with open(f"{TEST_DATA_DIR}/OPTIONS.json", "r") as payload:
            data = json.load(payload)
            assert expected_option_codes == parse_trim_line_codes(data)

    @patch("src.price_monitor.price_scraper.mercedes_benz.parser.get_option_codes")
    def test_parse_line_options_returns_type_with_the_whole_hierarchy_when_toggle_is_on(
        self, mock_get_option_codes
    ):
        mock_get_option_codes.return_value = ["SA-256"]
        data = {
            "componentCategories": "SA-256",
            "components": {
                "SA-256": {
                    "id": "SA-256",
                    "name": "AMG TRACK PACE",
                    "path": ["MULTIMEDIA_SAFETY", "MULTIMEDIA", "DISPLAY"],
                    "standard": True,
                    "enabled": True,
                    "selected": True,
                    "price": {
                        "netPrice": 0.0,
                        "price": 0.0,
                        "currencyISO": "EUR",
                    },
                }
            },
        }

        expected_line_option = create_test_line_item_option_code(
            code="SA-256",
            description="AMG TRACK PACE",
            type="MULTIMEDIA_SAFETY, MULTIMEDIA, DISPLAY",
        )
        actual_line_option = parse_line_options(True, data, True, "")[0]

        assert expected_line_option == actual_line_option

    @patch("src.price_monitor.price_scraper.mercedes_benz.parser.get_option_codes")
    def test_parse_line_options_returns_type_with_the_whole_hierarchy_when_toggle_is_off(
        self, mock_get_option_codes
    ):
        mock_get_option_codes.return_value = ["SA-256"]
        data = {
            "componentCategories": "SA-256",
            "components": {
                "SA-256": {
                    "id": "SA-256",
                    "name": "AMG TRACK PACE",
                    "path": ["MULTIMEDIA_SAFETY", "MULTIMEDIA", "DISPLAY"],
                    "standard": True,
                    "enabled": True,
                    "selected": True,
                    "price": {
                        "netPrice": 0.0,
                        "price": 0.0,
                        "currencyISO": "EUR",
                    },
                }
            },
        }

        expected_line_option = create_test_line_item_option_code(
            code="SA-256",
            description="AMG TRACK PACE",
            type="DISPLAY",
        )
        actual_line_option = parse_line_options(False, data, True, "")[0]

        assert expected_line_option == actual_line_option

    def test_parse_trim_line(self):
        expected_models_line_items = create_test_line_item(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="A-Klasse",
            model_range_code="W177",
            model_range_description="A-Klasse Kompakt-Limousine",
            model_code="1770841",
            model_description="A 180 Kompaktlimousine",
            line_code="1770841/PC-P59",
            line_description="Progressive",
            line_option_codes=[],
            currency="EUR",
            net_list_price=34270.0,
            gross_list_price=40781.3,
            on_the_road_price=40781.3,
            market=Market.DE,
        )
        with open(f"{TEST_DATA_DIR}/TRIM_LINE.json", "r") as payload:
            item = parse_trim_line(
                Market.DE, json.load(payload), "PC-P59", "Progressive", ""
            )
            assert item.asdict() == expected_models_line_items.asdict()

    @patch("src.price_monitor.price_scraper.mercedes_benz.parser.get_option_codes")
    def test_parse_line_options_does_not_return_line_when_line_is_not_basic(
        self, mock_get_option_codes
    ):
        mock_get_option_codes.return_value = ["SA-256"]
        data = {
            "componentCategories": ["SA-256", "SA-226"],
            "components": {
                "SA-226": {
                    "id": "SA-226",
                    "name": "AMG Line",
                    "path": ["VARIANTS", "LINES", "ZK096"],
                    "standard": True,
                    "enabled": True,
                    "selected": True,
                    "price": {
                        "netPrice": 0.0,
                        "price": 0.0,
                        "currencyISO": "EUR",
                    },
                },
                "SA-256": {
                    "id": "SA-256",
                    "name": "AMG TRACK PACE",
                    "path": ["MULTIMEDIA_SAFETY", "MULTIMEDIA", "DISPLAY"],
                    "standard": True,
                    "enabled": True,
                    "selected": True,
                    "price": {
                        "netPrice": 0.0,
                        "price": 0.0,
                        "currencyISO": "EUR",
                    },
                },
            },
        }

        expected_line_option = create_test_line_item_option_code(
            code="SA-256",
            description="AMG TRACK PACE",
            type="MULTIMEDIA_SAFETY, MULTIMEDIA, DISPLAY",
        )
        actual_line_option = parse_line_options(True, data, True, "")[0]

        assert expected_line_option == actual_line_option

    def test_get_option_codes_does_not_return_line_as_option_when_line_is_not_basic(
        self,
    ):
        expected_option_codes = [
            "PC-PAZ",
            "PC-P60",
            "LU-799",
            "LU-956",
            "LU-197",
            "LU-922",
            "LU-992",
            "LU-040",
            "LU-149",
            "SA-RWZ",
            "SA-RQW",
            "SA-RWQ",
            "SA-RPF",
            "SA-R01",
            "SA-8R9",
            "SA-652",
            "PC-PAX",
            "SA-U50",
            "SA-597",
            "PC-PAF",
            "SA-550",
            "SA-846",
            "PC-PTF",
            "AU-651",
            "AU-851",
            "AU-859",
            "AU-861",
            "SA-U17",
            "SA-Y05",
            "SA-872",
            "SA-401",
            "SA-H08",
            "SA-51H",
            "SA-H67",
            "SA-H39",
            "SA-H20",
            "SA-H73",
            "SA-697",
            "SA-732",
            "SA-757",
            "SA-775",
            "SA-781",
            "SA-661",
            "SA-L6J",
            "SA-L6K",
            "SA-L6H",
            "SA-443",
            "SA-543",
            "SA-51U",
            "SA-59U",
            "SA-61U",
            "SA-580",
            "PC-P53",
            "SA-581",
            "PC-PSO",
            "PC-PSR",
            "SA-256",
            "SA-865",
            "SA-444",
            "PC-PAG",
            "PC-PBG",
            "SA-553",
            "PC-P47",
            "PC-PBH",
            "SA-682",
            "SA-293",
            "SA-9B6",
            "SA-B30",
            "SA-B80",
            "SA-9B7",
            "SA-U70",
            "SA-B07",
        ]
        with open(f"{TEST_DATA_DIR}/EQE_OFFROADER_OPTIONS.json", "r") as payload:
            data = json.load(payload)
            assert sorted(expected_option_codes) == get_option_codes(
                data["componentCategories"], False
            )

    def test_append_option_code(self):
        list_of_component_id = []
        component_id = [
            "PC-PUF",
            "PC-PAZ",
            "PC-PYF",
        ]
        expected_output = [
            "PC-PUF",
            "PC-PAZ",
        ]
        _append_option_code(component_id, list_of_component_id)
        assert expected_output == list_of_component_id

    def test_parse_trim_line_codes_when_option_codes_are_in_list(self):
        expected_option_codes = ["PC-PYH"]
        with open(f"{TEST_DATA_DIR}/EQE_LIMOUSINE_LANG_OPTIONS.json", "r") as payload:
            data = json.load(payload)
            assert expected_option_codes == parse_trim_line_codes(data)

    @patch("src.price_monitor.price_scraper.mercedes_benz.parser.get_option_codes")
    def test_parse_line_options_does_not_return_option_when_it_is_incompatible_with_given_line(
        self,
        mock_get_option_codes,
    ):
        mock_get_option_codes.return_value = ["SA-256"]
        data = {
            "componentCategories": "SA-256",
            "components": {
                "SA-256": {
                    "id": "SA-256",
                    "name": "AMG TRACK PACE",
                    "path": ["MULTIMEDIA_SAFETY", "MULTIMEDIA", "DISPLAY"],
                    "incompatibleWith": ["Progressive"],
                    "standard": True,
                    "enabled": True,
                    "selected": True,
                    "price": {
                        "price": 0.00,
                        "formattedPrice": "0,00 €",
                        "netPrice": 0.00,
                        "formattedNetPrice": "0,00 €",
                        "currencyISO": "EUR",
                    },
                }
            },
        }

        expected_line_option = []
        actual_line_option = parse_line_options(True, data, False, "Progressive")
        assert expected_line_option == actual_line_option

    @patch("src.price_monitor.price_scraper.mercedes_benz.parser.get_option_codes")
    def test_parse_line_options_does_not_return_option_when_path_type_length_is_less_than_or_equal_to_zero(
        self,
        mock_get_option_codes,
    ):
        mock_get_option_codes.return_value = ["SA-256"]
        data = {
            "componentCategories": "SA-256",
            "components": {
                "SA-256": {
                    "id": "SA-256",
                    "name": "AMG TRACK PACE",
                    "path": ["ZK02"],
                    "incompatibleWith": ["Progressive"],
                    "standard": True,
                    "enabled": True,
                    "selected": True,
                    "price": {
                        "price": 0.00,
                        "formattedPrice": "0,00 €",
                        "netPrice": 0.00,
                        "formattedNetPrice": "0,00 €",
                        "currencyISO": "EUR",
                    },
                }
            },
        }

        expected_line_option = []
        actual_line_option = parse_line_options(False, data, True, "Progressive")
        assert expected_line_option == actual_line_option

    def test_get_option_codes_with_standard_component_ids(self):
        expected_option_codes = [
            "PC-P14",
            "PC-P15",
            "PC-P29",
            "PC-P31",
            "PC-P55",
            "PC-P87",
            "PC-PDA",
            "PC-PSE",
            "PC-PSJ",
            "PC-PSK",
            "PC-PSN",
            "PC-PSO",
            "PC-PSR",
            "PC-PSS",
        ]

        with open(
            f"{TEST_DATA_DIR}/OPTIONS_WITH_STANDARD_COMPONENT_ID.json", "r"
        ) as payload:
            data = json.load(payload)
            assert sorted(expected_option_codes) == get_option_codes(
                data["componentCategories"], True
            )

    @patch("src.price_monitor.price_scraper.mercedes_benz.parser.get_option_codes")
    def test_parse_line_options_does_return_option_type_as_not_available_when_path_key_not_available(
        self, mock_get_option_codes
    ):
        mock_get_option_codes.return_value = ["SA-256"]
        data = {
            "componentCategories": "SA-256",
            "components": {
                "SA-256": {
                    "id": "SA-256",
                    "name": "AMG TRACK PACE",
                    "standard": True,
                    "enabled": True,
                    "selected": True,
                    "price": {
                        "netPrice": 0.0,
                        "price": 0.0,
                        "currencyISO": "EUR",
                    },
                }
            },
        }

        expected_line_option = create_test_line_item_option_code(
            code="SA-256",
            description="AMG TRACK PACE",
            type="N/A",
        )
        actual_line_option = parse_line_options(True, data, True, "")[0]

        assert expected_line_option == actual_line_option


def test_parse_engine_performance_kw_and_hp_when_different_patterns_pass_then_return_kw_hp_list():
    expected_ep = [
        [NOT_AVAILABLE, NOT_AVAILABLE],
        ["350 kW + 150 kW", "476 hp + 204 HP"],
        ["280 kW + bis zu 17 kW", "381 PS + 23 PS"],
        ["330 kW + bis zu 15 kW", "449 PS + 20 PS"],
        ["370 kW + 17 kW", "503 hp + 23 HP"],
        ["165 kW + 10 kW", "224 hk + 14 hk"],
        ["484 kW", "658 HP"],
        ["195 kW + 15 kW", "265 hp + 20 HP"],
        ["470 kW", "639 PS"],
        ["270 kW + 16 kW", "367 hk + 22 hk"],
        ["432 kW", "587 HP"],
        ["195 kW + bis zu 15 kW", "265 PS + 20 PS"],
        ["225 kW + bis zu 10 kW", "306 PS + 14 PS"],
        ["270 kW + 15 kW", "367 hp + 20 HP"],
        ["120 kW + bis zu 80 kW", "163 PS + 109 PS"],
        ["410 kW + bis zu 16 kW", "557 PS + 22 PS"],
        ["150 kW + bis zu 17 kW", "204 PS + 23 PS"],
        ["230 kW + bis zu 15 kW", "313 PS + 20 PS"],
        ["432 kW", "587 PS"],
        ["120 kW + 10 kW", "163 hk + 14 hk"],
        ["450 kW + 150 kW", "612 hk + 204 hk"],
        ["165 kW + bis zu 10 kW", "224 PS + 14 PS"],
        ["215 kW", "292 PS"],
        ["198 kW + bis zu 15 kW", "269 PS + 20 PS"],
        ["330 kW + 17 kW", "449 hk + 23 hk"],
        ["147 kW + bis zu 15 kW", "200 PS + 20 PS"],
        ["225 kW + 10 kW", "306 hk + 14 hk"],
        ["400 kW", "544 PS"],
        ["280 kW + 15 kW", "381 hp + 20 HP"],
        ["270 kW + bis zu 17 kW", "367 PS + 23 PS"],
        ["145 kW + 17 kW", "197 hk + 23 hk"],
        ["330 kW", "449 hk"],
        ["265 kW", "360 HP"],
        ["320 kW + 16 kW", "435 hk + 22 hk"],
        ["270 kW + 110 kW", "367 hp + 150 HP"],
        ["198 kW + 15 kW", "269 hp + 20 HP"],
        ["350 kW", "476 PS"],
        ["140 kW", "190 HP"],
        ["430 kW", "585 hp"],
        ["265 kW", "360 hk"],
        ["450 kW + 140 kW", "612 hp + 190 HP"],
        ["370 kW + bis zu 17 kW", "503 PS + 23 PS"],
        ["220 kW + bis zu 110 kW", "299 PS + 150 PS"],
        ["470 kW + 150 kW", "639 hk + 204 hk"],
        ["460 kW", "625 hk"],
        ["450 kW + 140 kW", "612 hk + 190 hk"],
        ["125 kW + bis zu 17 kW", "170 PS + 23 PS"],
        ["270 kW + bis zu 16 kW", "367 PS + 22 PS"],
        ["450 kW", "612 PS"],
        ["310 kW + 10 kW", "421 hk + 14 hk"],
        ["140 kW + 10 kW", "190 hk + 14 hk"],
        ["190 kW + 17 kW", "258 hp + 23 HP"],
        ["150 kW + 95 kW", "204 hp + 129 HP"],
        ["380 kW + bis zu 16 kW", "517 PS + 22 PS"],
        ["120 kW + 80 kW", "163 hk + 109 hk"],
        ["150 kW + 17 kW", "204 hp + 23 HP"],
        ["198 kW + 17 kW", "269 hp + 23 HP"],
        ["145 kW + bis zu 100 kW", "197 PS + 136 PS"],
        ["270 kW + 17 kW", "367 hk + 23 hk"],
        ["370 kW + 17 kW", "503 hk + 23 hk"],
        ["145 kW + 100 kW", "197 hp + 136 HP"],
        ["185 kW + 100 kW", "252 hp + 136 HP"],
        ["225 kW + 10 kW", "306 hp + 14 HP"],
        ["300 kW", "408 HP"],
        ["230 kW + 17 kW", "313 hp + 23 HP"],
        ["320 kW + bis zu 16 kW", "435 PS + 22 PS"],
        ["410 kW + 16 kW", "557 hk + 22 hk"],
        ["145 kW + 95 kW", "197 hk + 129 hk"],
        ["400 kW", "544 HP"],
        ["310 kW", "421 hk"],
        ["145 kW + 17 kW", "197 hp + 23 HP"],
        ["140 kW", "190 hp"],
        ["484 kW", "658 hk"],
        ["120 kW + 80 kW", "163 hp + 109 HP"],
        ["330 kW + 100 kW", "449 hk + 136 hk"],
        ["430 kW", "585 hk"],
        ["150 kW + 100 kW", "204 hp + 136 HP"],
        ["410 kW + 16 kW", "557 hp + 22 HP"],
        ["430 kW + bis zu 15 kW", "585 PS + 20 PS"],
        ["470 kW", "639 hk"],
        ["168 kW", "228 hk"],
        ["320 kW + bis zu 15 kW", "435 PS + 20 PS"],
        ["470 kW + 150 kW", "639 hp + 204 HP"],
        ["120 kW + bis zu 15 kW", "163 PS + 20 PS"],
        ["230 kW + bis zu 17 kW", "313 PS + 23 PS"],
        ["330 kW + bis zu 100 kW", "449 PS + 136 PS"],
        ["150 kW + 95 kW", "204 hk + 129 hk"],
        ["140 kW + bis zu 10 kW", "190 PS + 14 PS"],
        ["198 kW + bis zu 17 kW", "269 PS + 23 PS"],
        ["265 kW", "360 PS"],
        ["380 kW + 16 kW", "517 hk + 22 hk"],
        ["145 kW + bis zu 17 kW", "197 PS + 23 PS"],
        ["430 kW", "585 PS"],
        ["185 kW + 100 kW", "252 hk + 136 hk"],
        ["350 kW + bis zu 150 kW", "476 PS + 204 PS"],
        ["330 kW + bis zu 120 kW", "449 PS + 163 PS"],
        ["195 kW + 15 kW", "265 hk + 20 hk"],
        ["450 kW + 16 kW", "612 hp + 22 HP"],
        [NOT_AVAILABLE, NOT_AVAILABLE],
        ["120 kW + bis zu 10 kW", "163 PS + 14 PS"],
        ["198 kW + 17 kW", "269 hk + 23 hk"],
        ["280 kW + 17 kW", "381 hp + 23 HP"],
        ["110 kW", "150 hp"],
        ["150 kW + bis zu 100 kW", "204 PS + 136 PS"],
        ["150 kW + 17 kW", "204 hk + 23 hk"],
        ["430 kW + 15 kW", "585 hp + 20 HP"],
        ["270 kW + bis zu 110 kW", "367 PS + 150 PS"],
        ["400 kW", "544 hk"],
        ["270 kW + 17 kW", "367 hp + 23 HP"],
        ["85 kW", "116 PS"],
        ["470 kW + bis zu 150 kW", "639 PS + 204 PS"],
        ["270 kW + 110 kW", "367 hk + 150 hk"],
        ["350 kW", "476 hp"],
        ["150 kW + bis zu 95 kW", "204 PS + 129 PS"],
        ["330 kW + 15 kW", "449 hk + 20 hk"],
        ["100 kW + 10 kW", "136 hp + 14 HP"],
        ["100 kW + bis zu 10 kW", "136 PS + 14 PS"],
        ["484 kW", "658 PS"],
        ["450 kW", "612 hp"],
        ["110 kW", "150 hk"],
        ["432 kW", "587 hk"],
        ["330 kW + 17 kW", "449 hp + 23 HP"],
        ["215 kW", "292 hk"],
        ["185 kW + bis zu 100 kW", "252 PS + 136 PS"],
        ["330 kW", "449 PS"],
        ["120 kW + 10 kW", "163 hp + 14 HP"],
        ["270 kW + bis zu 15 kW", "367 PS + 20 PS"],
        ["330 kW + 120 kW", "449 hp + 163 HP"],
        ["145 kW + 95 kW", "197 hp + 129 HP"],
        ["450 kW + bis zu 16 kW", "612 PS + 22 PS"],
        ["460 kW", "625 PS"],
        ["460 kW", "625 HP"],
        ["320 kW + 15 kW", "435 hp + 20 HP"],
        ["140 kW", "190 hk"],
        ["168 kW", "228 PS"],
        ["145 kW + bis zu 95 kW", "197 PS + 129 PS"],
        ["280 kW + bis zu 15 kW", "381 PS + 20 PS"],
        ["310 kW + 10 kW", "421 hp + 14 HP"],
        ["310 kW", "421 PS"],
        ["230 kW + 17 kW", "313 hk + 23 hk"],
        ["180 kW", "245 PS"],
        ["270 kW + 15 kW", "367 hk + 20 hk"],
        ["168 kW", "228 HP"],
        ["140 kW", "190 PS"],
        ["470 kW", "639 hp"],
        ["330 kW + bis zu 17 kW", "449 PS + 23 PS"],
        ["300 kW", "408 PS"],
        ["150 kW + 100 kW", "204 hk + 136 hk"],
        ["280 kW + 17 kW", "381 hk + 23 hk"],
        ["350 kW", "476 hk"],
        ["330 kW + 15 kW", "449 hp + 20 HP"],
        ["450 kW + bis zu 140 kW", "612 PS + 190 PS"],
        ["450 kW + 16 kW", "612 hk + 22 hk"],
        ["280 kW + 15 kW", "381 hk + 20 hk"],
        ["450 kW + 150 kW", "612 hp + 204 HP"],
        ["190 kW + 17 kW", "258 hk + 23 hk"],
        ["330 kW + 120 kW", "449 hk + 163 hk"],
        ["147 kW + 15 kW", "200 hk + 20 hk"],
        ["450 kW + bis zu 150 kW", "612 PS + 204 PS"],
        ["190 kW + bis zu 17 kW", "258 PS + 23 PS"],
        ["110 kW", "150 PS"],
        ["300 kW", "408 hk"],
        ["185 kW + 95 kW", "252 hk + 129 hk"],
        ["310 kW", "421 hp"],
        ["185 kW + bis zu 95 kW", "252 PS + 129 PS"],
        ["430 kW + 15 kW", "585 hk + 20 hk"],
        ["350 kW + 150 kW", "476 hk + 204 hk"],
        ["215 kW", "292 HP"],
        ["145 kW + 100 kW", "197 hk + 136 hk"],
        ["147 kW + 15 kW", "200 hp + 20 HP"],
        ["310 kW + bis zu 10 kW", "421 PS + 14 PS"],
        ["450 kW", "612 hk"],
        [NOT_AVAILABLE, NOT_AVAILABLE],
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
    "src.price_monitor.price_scraper.mercedes_benz.parser.parse_engine_performance_kw_and_hp"
)
def test_split_engine_performance_when_anti_pattern_send_then_return_na_and_log(
    mock_parse_engine_performance_kw_and_hp,
):
    mock_parse_engine_performance_kw_and_hp.side_effect = Exception(
        "Something went wrong"
    )
    expected_result = (NOT_AVAILABLE, NOT_AVAILABLE)
    actual_result = split_engine_performance(
        "430 KW 340 PS", Market.UK, "A-CLASS", "A_CLASS/A-SUV", "450 AMG Premium Line"
    )
    assert actual_result == expected_result
