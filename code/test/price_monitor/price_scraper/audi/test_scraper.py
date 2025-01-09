import json
import unittest
from pathlib import Path
from test.price_monitor.utils.test_data_builder import (
    create_test_line_item,
    create_test_line_item_option_code,
)
from unittest.mock import Mock, call, patch

from requests import HTTPError

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.audi.scraper import (
    AudiScraper,
    _find_available_models_link,
)
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"


class TestAudiScraper(unittest.TestCase):
    @patch(
        "src.price_monitor.price_scraper.audi.scraper.AudiScraper._scrape_models_for_market"
    )
    def test_scrape_models_loads_yesterdays_data_when_scrape_models_for_market_returns_empty_list_of_models(
        self, mock_scrape_models_for_market
    ):
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        mock_scrape_models_for_market.return_value = []

        mock_line_item_repository = Mock()
        mock_line_item_repository.load_market.return_value = []

        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )

        audi_scraper.scrape_models(Market.DE)

        mock_line_item_repository.load_market.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
        )

    def test_audi_scraper_will_scrape_for_us_when_us_is_enable_supported_market(
        self,
    ):
        audi_scraper_config = {
            "scraper": {"enabled": {Vendor.AUDI: [Market.US, Market.DE]}}
        }

        mock_line_item_repository = Mock()

        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )

        assert audi_scraper.markets == [Market.US, Market.DE]

    @patch.object(AudiScraper, "_scrape_models_from_link")
    @patch("src.price_monitor.price_scraper.audi.scraper._find_available_models_link")
    def test__scrape_models_for_market_when_market_is_given_then_return_list_of_line_items(
        self, mock__find_available_models_link, mock__scrape_models_from_link
    ):
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        mock__scrape_models_from_link.side_effect = [
            [create_test_line_item(line_description="audi_line_item")],
            [create_test_line_item(line_description="audi_line_item")],
        ]
        mock__find_available_models_link.return_value = [
            ["/de/brand/de/neuwagen/a5/a5-coupe", "/de/brand/de/neuwagen/a6/a6-avant"],
            [],
        ]
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_market.return_value = []

        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        audi_scraper._scrape_models_for_market(market=Market.DE)

        assert mock__scrape_models_from_link.call_count == 2
        assert mock__find_available_models_link.call_count == 1

    @patch.object(AudiScraper, "_scrape_line_items")
    def test___scrape_models_from_link_should_call_scrape_line_items_then_return_latest_line_items(
        self, mock__scrape_line_items
    ):
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        mock_session = Mock()
        mock__scrape_line_items.return_value = [
            create_test_line_item(line_description="audi_line_item"),
            create_test_line_item(line_description="audi_line_item"),
            create_test_line_item(line_description="audi_line_item"),
        ]
        mock_line_item_repository = Mock()
        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        parsed_line_items = audi_scraper._scrape_models_from_link(
            "/de/brand/de/neuwagen/a5/a5-coupe"
        )
        assert mock_line_item_repository.call_count == 0
        assert mock__scrape_line_items.call_count == 1
        assert len(parsed_line_items) == 3

    @patch.object(AudiScraper, "_get_line_item_from_trim_line")
    @patch("src.price_monitor.price_scraper.audi.scraper.execute_request")
    def test__scrape_line_items_when_model_api_is_successful_then_return_latest_line_items(
        self, mock_execute_request, mock__get_line_item_from_trim_line
    ):
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        mock_session = Mock()
        mock__get_line_item_from_trim_line.side_effect = [
            create_test_line_item(line_description="audi_line_item"),
            create_test_line_item(line_description="audi_line_item"),
            None,
            create_test_line_item(line_description="audi_line_item"),
        ]
        carinfo = json.loads(
            open(f"{TEST_DATA_DIR}/etron_option_common_details.json").read()
        )
        trimlines = json.loads(open(f"{TEST_DATA_DIR}/trimlines.json").read())
        mock__get_line_item_from_trim_line.return_value = None
        mock_execute_request.side_effect = [trimlines, carinfo]
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_market.return_value = []
        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        parsed_line_items = audi_scraper._scrape_line_items(
            "https://www.audi.de/de/brand/de/neuwagen/a5/a5-coupe.carinfo.mv-0-1733.31.json",
            "/de/brand/de/neuwagen/a5/a5-coupe",
            "https://www.audi.de/de/brand/de/neuwagen/a5/a5-coupe.modelsinfo.mv-0-1733.31.json",
        )

        mock_execute_request.assert_has_calls(
            [
                call(
                    "get",
                    "https://www.audi.de/de/brand/de/neuwagen/a5/a5-coupe.modelsinfo.mv-0-1733.31.json",
                    mock_session,
                ),
                call(
                    "get",
                    "https://www.audi.de/de/brand/de/neuwagen/a5/a5-coupe.carinfo.mv-0-1733.31.json",
                    mock_session,
                ),
            ]
        )
        assert mock_execute_request.call_count == 2
        assert mock_line_item_repository.call_count == 0
        assert mock__get_line_item_from_trim_line.call_count == 4
        assert len(parsed_line_items) == 3

    @patch.object(AudiScraper, "_load_trim_lines_from_previous_day")
    @patch.object(AudiScraper, "_get_line_item_from_trim_line")
    @patch("src.price_monitor.price_scraper.audi.scraper.execute_request")
    def test__scrape_line_items_when_model_api_is_fails_then_return_previous_day_line_items(
        self,
        mock_execute_request,
        mock__get_line_item_from_trim_line,
        mock__load_trim_lines_from_previous_day,
    ):
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        mock_session = Mock()
        mock__load_trim_lines_from_previous_day.return_value = [
            create_test_line_item(line_description="audi_line_item"),
            create_test_line_item(line_description="audi_line_item"),
            create_test_line_item(line_description="audi_line_item"),
        ]
        trimlines = json.loads(open(f"{TEST_DATA_DIR}/trimlines.json").read())
        mock__get_line_item_from_trim_line.return_value = None
        mock_execute_request.side_effect = [trimlines, HTTPError()]
        mock_line_item_repository = Mock()
        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)
        setattr(
            audi_scraper, "link_not_having_price", ["/de/brand/de/neuwagen/a5/a5-coupe"]
        )

        parsed_line_items = audi_scraper._scrape_line_items(
            "https://www.audi.de/de/brand/de/neuwagen/a5/a5-coupe.carinfo.mv-0-1733.31.json",
            "/de/brand/de/neuwagen/a5/a5-coupe",
            "https://www.audi.de/de/brand/de/neuwagen/a5/a5-coupe.modelsinfo.mv-0-1733.31.json",
        )

        assert mock_execute_request.call_count == 2
        mock__load_trim_lines_from_previous_day.assert_called_with(
            "/de/brand/de/neuwagen/a5/a5-coupe"
        )
        assert len(parsed_line_items) == 3

    def test__load_trim_lines_from_previous_day_should_call_load_model_filter_by_model_range_code(
        self,
    ):
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_model_filter_by_model_range_code.return_value = [
            create_test_line_item(line_description="audi_line_item"),
            create_test_line_item(line_description="audi_line_item"),
            create_test_line_item(line_description="audi_line_item"),
        ]
        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        parsed_line_items = audi_scraper._load_trim_lines_from_previous_day(
            "/de/brand/de/neuwagen/a5/a5-coupe",
        )

        mock_line_item_repository.load_model_filter_by_model_range_code.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
            series="a5",
            model_range_code="a5-coupe",
        )
        assert len(parsed_line_items) == 3

    @patch("src.price_monitor.price_scraper.audi.scraper.parse_model_line_item")
    @patch.object(AudiScraper, "_load_previous_day_line_item")
    @patch.object(AudiScraper, "get_line_option_codes")
    @patch.object(AudiScraper, "_get_trim_line_json")
    def test__get_line_item_from_trim_line_when_there_is_no_error_then_return_today_line_item(
        self,
        mock__get_trim_line_json,
        mock_get_line_option_codes,
        mock__load_previous_day_line_item,
        mock_parse_model_line_item,
    ):
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        mock_session = Mock()
        mock__get_trim_line_json.return_value = "test_json_data"
        line_item = create_test_line_item(line_description="audi_line_item")
        mock_parse_model_line_item.return_value = line_item
        mock_get_line_option_codes.return_value = [
            create_test_line_item_option_code(type="Wheel")
        ]
        mock_line_item_repository = Mock()
        mock__load_previous_day_line_item.return_value = None
        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        parsed_line_item = audi_scraper._get_line_item_from_trim_line(
            "/de/brand/de/neuwagen/a5/a5-coupe",
            "FR5J043",
            "FR5K043",
            "FR5K043%7C6Y6Y%7CYM",
            {"carinfo": "carinfo"},
        )

        assert mock__load_previous_day_line_item.call_count == 0
        assert parsed_line_item.asdict() == line_item.asdict()
        mock_get_line_option_codes.assert_called_with(
            model_link="/de/brand/de/neuwagen/a5/a5-coupe",
            trimline_code="FR5K043",
            trimline_details="test_json_data",
            carinfo={"carinfo": "carinfo"},
        )
        mock_parse_model_line_item.assert_called_with(
            model_link="/de/brand/de/neuwagen/a5/a5-coupe",
            model_code="FR5J043",
            model_configuration="test_json_data",
            market=Market.DE,
        )
        mock__get_trim_line_json.assert_called_with(
            "FR5J043", "FR5K043", "FR5K043%7C6Y6Y%7CYM"
        )

    @patch.object(AudiScraper, "_load_previous_day_line_item")
    @patch.object(AudiScraper, "_get_trim_line_json")
    def test__get_line_item_from_trim_line_when_there_is_an_error_then_return_yesterday_line_item(
        self, mock__get_trim_line_json, mock__load_previous_day_line_item
    ):
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        mock_session = Mock()
        mock__get_trim_line_json.side_effect = HTTPError()
        line_item = create_test_line_item(line_description="audi_line_item")
        mock_line_item_repository = Mock()
        mock__load_previous_day_line_item.return_value = line_item
        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        parsed_line_item = audi_scraper._get_line_item_from_trim_line(
            "/de/brand/de/neuwagen/a5/a5-coupe",
            "FR5J043",
            "FR5K043",
            "FR5K043%7C6Y6Y%7CYM",
            {"carinfo": "carinfo"},
        )

        mock__load_previous_day_line_item.assert_called_with(
            "/de/brand/de/neuwagen/a5/a5-coupe", "FR5K043"
        )
        mock__get_trim_line_json.assert_called_with(
            "FR5J043", "FR5K043", "FR5K043%7C6Y6Y%7CYM"
        )
        assert mock__load_previous_day_line_item.call_count == 1
        assert parsed_line_item.asdict() == line_item.asdict()

    def test__load_previous_day_line_item_when_load_1_item_then_return_that_line_item(
        self,
    ):
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        mock_session = Mock()
        mock_line_item_repository = Mock()
        expected_line_item = create_test_line_item(line_description="audi_line_item")
        mock_line_item_repository.load_model_filter_by_line_code.return_value = [
            expected_line_item,
        ]

        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        parsed_line_item = audi_scraper._load_previous_day_line_item(
            "/de/brand/de/neuwagen/a5/a5-coupe", "FR3FJ"
        )

        mock_line_item_repository.load_model_filter_by_line_code.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
            line_code="FR3FJ",
        )
        assert expected_line_item.asdict() == parsed_line_item.asdict()

    def test__load_previous_day_line_item_when_load_0_item_then_return_none(self):
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_model_filter_by_line_code.return_value = []

        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        parsed_line_item = audi_scraper._load_previous_day_line_item(
            "/de/brand/de/neuwagen/a5/a5-coupe", "FR3FJ"
        )

        mock_line_item_repository.load_model_filter_by_line_code.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
            line_code="FR3FJ",
        )
        assert parsed_line_item is None

    def test__load_previous_day_line_item_when_load_more_than_1_item_then_return_none(
        self,
    ):
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        mock_session = Mock()
        mock_line_item_repository = Mock()
        expected_line_item = create_test_line_item(line_description="audi_line_item")
        mock_line_item_repository.load_model_filter_by_line_code.return_value = [
            expected_line_item,
            expected_line_item,
        ]

        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        parsed_line_item = audi_scraper._load_previous_day_line_item(
            "/de/brand/de/neuwagen/a5/a5-coupe", "FR3FJ"
        )

        mock_line_item_repository.load_model_filter_by_line_code.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
            line_code="FR3FJ",
        )
        assert parsed_line_item is None

    @patch("src.price_monitor.price_scraper.audi.scraper.execute_request")
    def test__get_trim_line_json_when_api_execute_successful_then_return_json_response(
        self, mock_execute_request
    ):
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_execute_request.return_value = "trimline_details_json"
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        response = audi_scraper._get_trim_line_json(
            model_code="FR5J043", trimline_code="FR5K043", params="FR5J043%7C6Y6Y%7CYM"
        )

        assert response == "trimline_details_json"
        mock_execute_request.assert_called_with(
            "get",
            "https://www.audi.de/ak4/bin/dpu-de/configuration?context=nemo-de%3Ade&ids=FR5J043%7C6Y6Y%7CYM&set=FR5K043",
            mock_session,
        )

    @patch(
        "src.price_monitor.price_scraper.audi.scraper.parse_line_item_options_for_trimline"
    )
    @patch.object(AudiScraper, "get_options_types")
    def test_get_line_option_codes_when_able_to_fetch_options_and_their_generic_option_type_then_return_list_of_line_option_codes(
        self, mock_get_options_types, mock_parse_line_item_options_for_trimline
    ):
        options_type = {"1YA": "Wheel", "YM": "Metalic Color"}
        mock_get_options_types.return_value = options_type
        expected_line_option_codes = [
            create_test_line_item_option_code(code="1YA"),
            create_test_line_item_option_code(code="YM"),
        ]
        mock_parse_line_item_options_for_trimline.return_value = (
            expected_line_option_codes
        )
        mock_session = Mock()
        mock_line_item_repository = Mock()
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        actual_line_option_codes = audi_scraper.get_line_option_codes(
            model_link="de/brand/de/neuwagen/a5/a5-coupe.modelsinfo.mv-0-1733.31.json",
            trimline_code="FR45FKF",
            trimline_details="trimline_details",
            carinfo={"items": "line_option_codes"},
        )
        for actual in actual_line_option_codes:
            assert actual.type == options_type[actual.code]
        mock_get_options_types.assert_called_with({"items": "line_option_codes"})
        mock_parse_line_item_options_for_trimline.assert_called_with(
            "trimline_details", "line_option_codes", Market.DE
        )

    @patch("src.price_monitor.price_scraper.audi.scraper.parse_options_type")
    @patch("src.price_monitor.price_scraper.audi.scraper.get_option_type_details")
    def test_get_options_types_when_api_execute_successful_then_return_dict_of_option_types(
        self, mock_get_option_type_details, mock_parse_options_type
    ):
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_get_option_type_details.return_value = {"data": "option_type_json"}
        expected_option_types = {"1YA": "Wheel", "YM": "Metalic Color"}
        mock_parse_options_type.return_value = expected_option_types
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        response = audi_scraper.get_options_types(carinfo="carinfo")

        assert response == expected_option_types
        mock_get_option_type_details.assert_called_with("carinfo", mock_session)

    @patch("src.price_monitor.price_scraper.audi.scraper.get_option_type_details")
    def test_get_options_types_when_there_is_no_data_in_response_then_raise_exception(
        self, mock_get_option_type_details
    ):
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_get_option_type_details.return_value = {"error": "something went wrong."}
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        with self.assertRaises(ValueError):
            audi_scraper.get_options_types(carinfo="carinfo")

        mock_get_option_type_details.assert_called_with("carinfo", mock_session)

    @patch("src.price_monitor.price_scraper.audi.scraper.parse_available_model_links")
    @patch("src.price_monitor.price_scraper.audi.scraper.execute_request")
    def test__find_available_models_link_when_api_is_successful_then_return_list_of_model_links(
        self, mock_execute_request, mock_parse_available_model_links
    ):
        mock_session = Mock()
        expected_models_link = ["model_link_1", "model_link_2"]
        mock_execute_request.return_value = "homepage_data"
        mock_parse_available_model_links.return_value = expected_models_link
        actual_models_link = _find_available_models_link(mock_session, Market.DE)

        mock_execute_request.assert_called_with(
            "get",
            "https://www.audi.de/de/brand/de/neuwagen.html",
            mock_session,
            response_format="text",
        )
        mock_parse_available_model_links.assert_called_with("homepage_data")
        expected_models_link == actual_models_link

    @patch("src.price_monitor.price_scraper.audi.scraper.execute_request")
    def test__get_trim_line_json_when_conflicts_in_api_response_then_execute_resolved_url(
        self, mock_execute_request
    ):
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_execute_request.side_effect = [
            {"conflicts": {"prstring": "FBACFG1_2024|B4B4|AW"}},
            "trimline_details_json",
        ]
        audi_scraper_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.DE]}}}
        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )
        setattr(audi_scraper, "session", mock_session)
        setattr(audi_scraper, "market", Market.DE)

        response = audi_scraper._get_trim_line_json(
            model_code="FR5J043", trimline_code="FR5K043", params="FR5J043%7C6Y6Y%7CYM"
        )

        assert response == "trimline_details_json"
        assert mock_execute_request.call_count == 2
        mock_execute_request.assert_has_calls(
            [
                call(
                    "get",
                    "https://www.audi.de/ak4/bin/dpu-de/configuration?context=nemo-de%3Ade&ids=FR5J043%7C6Y6Y%7CYM&set=FR5K043",
                    mock_session,
                ),
                call(
                    "get",
                    "https://www.audi.de/ak4/bin/dpu-de/configuration?context=nemo-de%3Ade",
                    mock_session,
                    body={"ids": "FBACFG1_2024|B4B4|AW"},
                ),
            ]
        )
