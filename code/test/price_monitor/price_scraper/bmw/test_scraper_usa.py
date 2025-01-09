import unittest
from test.price_monitor.utils.test_data_builder import (
    create_test_line_item,
    create_test_line_item_option_code,
)
from unittest.mock import Mock, patch

from requests import HTTPError

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.price_scraper.bmw.scraper_usa import (
    _scrape_line_options,
    get_line_items_for_model,
    get_line_options,
    get_line_specific_details,
    get_model_details,
    is_option_constructible_for_line,
    scrape_models_for_usa,
)
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


class TestBMWScraperUsa(unittest.TestCase):
    scraper_config = {"scraper": {"enabled": [Vendor.BMW], "markets": [Market.US]}}

    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_line_items_for_model")
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_model_details")
    @patch(
        "src.price_monitor.price_scraper.bmw.scraper_usa.parse_model_code_list_from_json"
    )
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.execute_request")
    def test_scrape_models_for_usa_when_market_is_us_returns_list_of_line_items_for_us_market(
        self,
        mock_execute_request,
        mock_parse_model_code_list_from_json,
        mock_get_model_details,
        mock_get_line_items_for_model,
    ):
        expected_result = [create_test_line_item(vendor=Vendor.BMW, market=Market.US)]
        mock_execute_request.return_value = "I am data"
        data = Mock(text="Best Model Ever")
        data = data.json()
        mock_parse_model_code_list_from_json.return_value = ["model_code"]
        mock_get_model_details.return_value = data
        mock_get_line_items_for_model.return_value = expected_result

        result = scrape_models_for_usa(
            line_item_repository=FileSystemLineItemRepository, config={}
        )

        assert expected_result == result

    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_line_items_for_model")
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_model_details")
    @patch(
        "src.price_monitor.price_scraper.bmw.scraper_usa.parse_model_code_list_from_json"
    )
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.execute_request")
    def test_scrape_models_for_usa_calls_get_model_detail_when_api_is_successful(
        self,
        mock_execute_request,
        mock_parse_model_code_list_from_json,
        mock_get_model_details,
        mock_get_line_items_for_model,
    ):
        expected_result = [create_test_line_item(vendor=Vendor.BMW, market=Market.US)]
        mock_execute_request.return_value = "I am data"
        data = Mock(text="Best Model Ever")
        data = data.json()
        mock_parse_model_code_list_from_json.return_value = ["model_code"]
        mock_get_model_details.return_value = data
        mock_get_line_items_for_model.return_value = expected_result

        result = scrape_models_for_usa(
            line_item_repository=FileSystemLineItemRepository, config={}
        )

        assert expected_result == result
        assert mock_get_model_details.call_count == 1

    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.execute_request")
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_line_items_for_model")
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_model_details")
    @patch(
        "src.price_monitor.price_scraper.bmw.scraper_usa.parse_model_code_list_from_json"
    )
    def test_scrape_models_for_usa_calls_load_model_filter_by_model_code_when_api_fails(
        self,
        mock_parse_model_code_list_from_json,
        mock_get_model_details,
        mock_get_line_items_for_model,
        mock_execute_request,
    ):
        expected_result = [create_test_line_item(vendor=Vendor.BMW, market=Market.US)]
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_model_filter_by_model_code.return_value = [
            create_test_line_item(vendor=Vendor.BMW, market=Market.US)
        ]
        mock_execute_request.return_value = "model_list_json"
        mock_get_model_details.side_effect = Exception()
        mock_parse_model_code_list_from_json.return_value = ["model_code"]
        mock_get_line_items_for_model.return_value = expected_result

        scrape_models_for_usa(line_item_repository=mock_line_item_repository, config={})

        mock_line_item_repository.load_model_filter_by_model_code.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.BMW,
            model_code="model_code",
        )

    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.execute_request")
    def test_get_model_details_when_given_model_code_returns_the_scraped_json_for_model_code(
        self, mock_execute_request
    ):
        expected_result = Mock("I am data")
        mock_session = Mock()
        mock_execute_request.return_value = expected_result

        result = get_model_details("model_code", mock_session)

        assert expected_result == result

    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_line_options")
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.extract_price")
    def test_scrape_line_options_calls_get_line_options_when_api_is_successful(
        self,
        mock_extract_price,
        mock_get_line_options,
    ):
        mock_session = Mock()
        model_details: dict = {"cmId": "model_key"}
        model_key = "model_key"
        line_item = create_test_line_item(vendor=Vendor.BMW, market=Market.US)
        mock_get_line_options.return_value = []
        mock_extract_price.return_value = 0.00

        _scrape_line_options(
            {},
            line_item,
            FileSystemLineItemRepository,
            Market.US,
            model_details,
            model_key,
            mock_session,
        )

        mock_get_line_options.assert_called_with(
            {}, model_details, model_key, mock_session
        )

    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_line_options")
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.extract_price")
    def test_scrape_line_options_calls_load_line_option_codes_for_line_code_when_api_fails(
        self,
        mock_extract_price,
        mock_get_line_options,
    ):
        line_item = create_test_line_item(
            vendor=Vendor.BMW,
            market=Market.US,
            model_code="model_code",
            line_code="line_code",
        )
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_line_option_codes_for_line_code.return_value = []
        model_details: dict = {"cmId": "model_key"}
        mock_get_line_options.side_effect = Exception()
        mock_extract_price.return_value = 0.00

        _scrape_line_options(
            {},
            line_item,
            mock_line_item_repository,
            Market.US,
            model_details,
            "model_key",
            mock_session,
        )

        mock_line_item_repository.load_line_option_codes_for_line_code.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.BMW,
            model_code="model_code",
            line_code="line_code",
        )

    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.execute_request")
    def test_get_line_specific_details_when_line_is_not_basic_then_execute_request(
        self, mock_execute_request
    ):
        mock_session = Mock()
        model_details = {
            "model": {
                "name": "model_name",
                "series": "model_series",
                "bodyStyle": "model_body_style",
            }
        }
        mock_execute_request.return_value = "line_item_details"

        line_details = get_line_specific_details(
            model_details,
            create_test_line_item(vendor=Vendor.BMW),
            "model_key",
            mock_session,
        )

        assert mock_execute_request.call_count == 2
        assert line_details == "line_item_details"

    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.execute_request")
    def test_get_line_specific_details_when_line_is_basic_then_return_model_details_itself(
        self, mock_execute_request
    ):
        mock_session = Mock()
        model_details = {
            "model": {
                "name": "model_name",
                "series": "model_series",
                "bodyStyle": "model_body_style",
            }
        }

        line_details = get_line_specific_details(
            model_details,
            create_test_line_item(vendor=Vendor.BMW, line_code="BASIC_LINE"),
            "model_key",
            mock_session,
        )

        assert mock_execute_request.call_count == 0
        assert line_details == model_details

    @patch(
        "src.price_monitor.price_scraper.bmw.scraper_usa.is_option_constructible_for_line"
    )
    @patch(
        "src.price_monitor.price_scraper.bmw.scraper_usa.parse_all_available_options"
    )
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.parse_extra_designs_list")
    def test_get_line_options_when_is_option_constructible_for_line_returns_true(
        self,
        mock_parse_extra_designs_list,
        mock_parse_all_available_options,
        mock_is_option_constructible_for_line,
    ):
        expected_result = ["constructable_option"]
        line_details = {}
        model_details = {"optionDetails": "option_details"}
        model_key = "model_key"
        mock_session = Mock()
        mock_parse_extra_designs_list.return_value = []
        mock_is_option_constructible_for_line.return_value = True
        mock_parse_all_available_options.return_value = expected_result
        result = get_line_options(line_details, model_details, model_key, mock_session)

        mock_is_option_constructible_for_line.assert_called_with(
            [], "model_key", "constructable_option", mock_session
        )
        assert expected_result == result

    @patch(
        "src.price_monitor.price_scraper.bmw.scraper_usa.is_option_constructible_for_line"
    )
    @patch(
        "src.price_monitor.price_scraper.bmw.scraper_usa.parse_all_available_options"
    )
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.parse_extra_designs_list")
    def test_get_line_options_when_is_option_constructible_for_line_returns_false(
        self,
        mock_parse_extra_designs_list,
        mock_parse_all_available_options,
        mock_is_option_constructible_for_line,
    ):
        expected_result = []
        line_details = {}
        model_details = {"optionDetails": "option_details"}
        model_key = "model_key"
        mock_session = Mock()
        mock_parse_extra_designs_list.return_value = []
        mock_is_option_constructible_for_line.return_value = False
        mock_parse_all_available_options.return_value = ["constructable_option"]
        result = get_line_options(line_details, model_details, model_key, mock_session)

        mock_is_option_constructible_for_line.assert_called_with(
            [], "model_key", "constructable_option", mock_session
        )
        assert expected_result == result

    @patch(
        "src.price_monitor.price_scraper.bmw.scraper_usa.parse_is_option_constructible"
    )
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.execute_request")
    def test_is_option_constructible_for_line_returns_true_when_option_is_constructable(
        self, mock_execute_request, mock_parse_is_option_constructible
    ):
        expected_result = True
        mock_session = Mock()
        mock_execute_request.return_value = Mock("I am data")
        mock_parse_is_option_constructible.return_value = expected_result
        result = is_option_constructible_for_line(
            [],
            "model_key",
            create_test_line_item_option_code(code="code"),
            mock_session,
        )
        assert expected_result == result

    @patch(
        "src.price_monitor.price_scraper.bmw.scraper_usa.parse_is_option_constructible"
    )
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.execute_request")
    def test_is_option_constructible_for_line_returns_false_when_option_is_not_constructable(
        self, mock_execute_request, mock_parse_is_option_constructible
    ):
        expected_result = False
        mock_session = Mock()
        mock_execute_request.return_value = Mock("I am data")
        mock_parse_is_option_constructible.return_value = expected_result
        result = is_option_constructible_for_line(
            [],
            "model_key",
            create_test_line_item_option_code(code="code"),
            mock_session,
        )
        assert expected_result == result

    @patch("src.price_monitor.price_scraper.bmw.scraper_usa._scrape_line_options")
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.extract_price")
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_line_specific_details")
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.parse_line_items")
    def test_get_line_items_for_model_calls_get_line_specific_details_when_api_is_successful(
        self,
        mock_parse_line_items,
        mock_get_line_specific_details,
        mock_extract_price,
        mock_scrape_line_options,
    ):
        mock_session = Mock()
        model_details: dict = {"cmId": "model_key"}
        model_key = "model_key"
        line_item = create_test_line_item(vendor=Vendor.BMW, market=Market.US)
        mock_parse_line_items.return_value = [line_item]
        mock_get_line_specific_details.return_value = {}
        mock_scrape_line_options.return_value = []
        mock_extract_price.return_value = 0.00

        get_line_items_for_model(
            Market.US, model_details, mock_session, FileSystemLineItemRepository
        )

        mock_get_line_specific_details.assert_called_with(
            model_details, line_item, model_key, mock_session
        )

    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_line_specific_details")
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.parse_line_items")
    def test_get_line_items_for_model_calls_load_model_filter_by_trim_line_when_api_fails_returns_line_item_list(
        self,
        mock_parse_line_items,
        mock_get_line_specific_details,
    ):
        line_item = create_test_line_item(
            vendor=Vendor.BMW,
            market=Market.US,
            series="series",
            model_code="model_code",
            line_code="line_code",
        )
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_model_filter_by_trim_line.return_value = [
            line_item
        ]
        model_details: dict = {"cmId": "model_key"}
        mock_parse_line_items.return_value = [line_item]
        mock_get_line_specific_details.side_effect = Exception()

        get_line_items_for_model(
            Market.US, model_details, mock_session, mock_line_item_repository
        )

        mock_line_item_repository.load_model_filter_by_trim_line.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.BMW,
            model_code="model_code",
            line_code="line_code",
        )

    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_line_specific_details")
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.parse_line_items")
    def test_get_line_items_for_model_calls_load_model_filter_by_trim_line_when_api_fails_returns_empty_list(
        self,
        mock_parse_line_items,
        mock_get_line_specific_details,
    ):
        line_item = create_test_line_item(
            vendor=Vendor.BMW,
            market=Market.US,
            series="series",
            model_code="model_code",
            line_code="line_code",
        )
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_model_filter_by_trim_line.return_value = []
        model_details: dict = {"cmId": "model_key"}
        mock_parse_line_items.return_value = [line_item]
        mock_get_line_specific_details.side_effect = Exception()

        get_line_items_for_model(
            Market.US, model_details, mock_session, mock_line_item_repository
        )

        mock_line_item_repository.load_model_filter_by_trim_line.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.BMW,
            model_code="model_code",
            line_code="line_code",
        )

    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_line_items_for_model")
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.get_model_details")
    @patch(
        "src.price_monitor.price_scraper.bmw.scraper_usa.parse_model_code_list_from_json"
    )
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.execute_request")
    def test_scrape_models_for_usa_when_run_for_two_model_then_return_their_collated_line_items(
        self,
        mock_execute_request,
        mock_parse_model_code_list_from_json,
        mock_get_model_details,
        mock_get_line_items_for_model,
    ):
        model_1_line_items = [create_test_line_item(), create_test_line_item()]
        model_2_line_items = [create_test_line_item()]
        expected_line_items = model_1_line_items + model_2_line_items
        mock_execute_request.return_value = "I am data"
        mock_parse_model_code_list_from_json.return_value = [
            "model_code1",
            "model_code2",
        ]
        mock_get_line_items_for_model.side_effect = [
            model_1_line_items,
            model_2_line_items,
        ]
        mock_get_model_details.return_value = ""

        actual_line_items = scrape_models_for_usa(
            line_item_repository=FileSystemLineItemRepository, config={}
        )

        assert expected_line_items == actual_line_items
        assert mock_get_model_details.call_count == 2

    @patch(
        "src.price_monitor.price_scraper.bmw.scraper_usa.parse_is_option_constructible"
    )
    @patch("src.price_monitor.price_scraper.bmw.scraper_usa.execute_request")
    def test_get_line_options_when_is_not_able_to_undo_with_put_then_try_with_delete_method(
        self, mock_execute_request, mock_parse_is_option_constructible
    ):
        expected_result = True
        mock_session = Mock()
        mock_execute_request.side_effect = [
            Mock("I am data"),
            HTTPError(),
            Mock("I am data"),
        ]
        mock_parse_is_option_constructible.return_value = expected_result
        result = is_option_constructible_for_line(
            [],
            "model_key",
            create_test_line_item_option_code(code="code"),
            mock_session,
        )
        assert expected_result == result
