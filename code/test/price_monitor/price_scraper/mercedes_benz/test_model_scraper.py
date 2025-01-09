import unittest
from test.price_monitor.utils.test_data_builder import create_test_line_item
from unittest.mock import Mock, patch

from requests.exceptions import HTTPError

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.price_scraper.mercedes_benz.model_scraper import ModelScraper
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


class TestModelScraper(unittest.TestCase):
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.ModelScraper._scrape_trim_line"
    )
    def test__append_trim_line_calls_load_model_filter_by_line_code_when_api_fails(
        self, mock_execute_request
    ):
        basic_line = create_test_line_item(
            vendor=Vendor.MERCEDES_BENZ, market=Market.DE, model_code="model_code"
        )
        model_options = {
            "components": {"line_code": {"name": "trim_line_name", "selected": True}}
        }
        trim_line_codes = ["line_code"]
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_model_filter_by_line_code.return_value = [
            create_test_line_item(line_description="line_description")
        ]
        mock_execute_request.side_effect = HTTPError()

        model_scraper = ModelScraper(
            market=Market.DE,
            session=mock_session,
            line_item_repository=mock_line_item_repository,
        )

        model_scraper._append_trim_lines(
            basic_line, model_options, trim_line_codes, "vehicle_id", "version", ""
        )

        mock_line_item_repository.load_model_filter_by_line_code.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.MERCEDES_BENZ,
            line_code="model_code/line_code",
        )

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.ModelScraper._scrape_trim_line"
    )
    def test__append_trim_line_calls_scrape_trim_when_api_is_successful(
        self, mock_scrape_trim_line
    ):
        expected_model = [
            create_test_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.DE,
                model_code="model_code",
                line_code="line_code",
            )
        ]
        basic_line = create_test_line_item(
            vendor=Vendor.MERCEDES_BENZ, market=Market.DE, model_code="model_code"
        )
        model_options = {
            "components": {"line_code": {"name": "trim_line_name", "selected": True}}
        }
        trim_line_codes = ["line_code"]
        mock_session = Mock()
        mock_scrape_trim_line.return_value = expected_model

        model_scraper = ModelScraper(
            market=Market.DE,
            session=mock_session,
            line_item_repository=FileSystemLineItemRepository,
        )

        model_scraper._append_trim_lines(
            basic_line, model_options, trim_line_codes, "vehicle_id", "version", ""
        )

        mock_scrape_trim_line.assert_called_with(
            "vehicle_id", "line_code", "trim_line_name", "version", ""
        )

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.ModelScraper._scrape_options"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.parse_trim_line"
    )
    def test__get_trim_line_calls_load_model_filter_by_line_code_when_api_fails(
        self, mock_parse_trim_line, mock_execute_request
    ):
        mock_session = Mock()
        data = Mock(text="Model Mercedes Best You've Ever Seen")
        data = data.json()
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_line_option_codes_for_line_code.return_value = []
        mock_parse_trim_line.return_value = create_test_line_item(
            vendor=Vendor.MERCEDES_BENZ,
            market=Market.DE,
            model_code="model_code",
            line_code="line_code",
            model_description="model_description",
            line_description="line_description",
        )
        mock_execute_request.side_effect = HTTPError()

        model_scraper = ModelScraper(
            market=Market.DE,
            session=mock_session,
            line_item_repository=mock_line_item_repository,
        )

        model_scraper._get_trim_line(
            data, "line_code", "line_description", "version", ""
        )

        mock_line_item_repository.load_line_option_codes_for_line_code.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.MERCEDES_BENZ,
            series="test",
            model_code="model_code",
            line_code="line_code",
        )

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.parse_trim_line"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.ModelScraper._scrape_options"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.parse_line_options"
    )
    def test__get_trim_line_calls_scrape_options_when_the_api_call_is_successful(
        self, mock_parse_trim_line, mock_scrape_options, mock_parse_line_options
    ):
        mock_session = Mock()
        vehicle = {"vehicle": {"vehicleId": "vehicle_id"}}
        mock_scrape_options.return_value = []
        mock_parse_trim_line.return_value = []

        model_scraper = ModelScraper(
            market=Market.DE,
            session=mock_session,
            line_item_repository=FileSystemLineItemRepository,
        )

        model_scraper._get_trim_line(
            vehicle, "line_code", "line_description", "version", ""
        )

        mock_scrape_options.assert_called_with("vehicle_id", "version")

    @patch("src.price_monitor.price_scraper.mercedes_benz.model_scraper.logger")
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.ModelScraper._get_trim_line_codes"
    )
    def test_get_model_calls_load_model_filter_by_model_description_when_api_fails(
        self, mock_execute_request, mock_logger
    ):
        data = {
            "classBodyNames": ["classBodyName"],
            "vehicles": [
                {
                    "vehicleId": "vehicle_id",
                    "name": "model_description",
                    "baumuster": "model_code",
                    "tags": [{"value": ""}],
                }
            ],
        }
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_model_filter_by_model_code.return_value = [
            create_test_line_item()
        ]
        model_scraper = ModelScraper(
            market=Market.DE,
            session=mock_session,
            line_item_repository=mock_line_item_repository,
        )
        mock_execute_request.side_effect = HTTPError()

        model_scraper.get_model(data, "version")

        mock_line_item_repository.load_model_filter_by_model_code.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.MERCEDES_BENZ,
            model_code="model_code",
        )
        mock_logger.error.assert_called_with(
            "[DE] Failed to scrape trim lines for model: model_description for mercedes_benz.Reason: ''."
            " Loading options from previous dataset..."
        )
        mock_logger.info.assert_called_with(
            "[DE] Loaded 1 trim lines for model: model_description for mercedes_benz."
        )

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.ModelScraper._get_basic_line"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.ModelScraper._get_trim_line_codes"
    )
    def test_get_model_calls_get_trim_line_codes_when_api_is_successful(
        self, mock_get_trim_line_codes, mock_get_basic_line
    ):
        data = {
            "classBodyNames": ["classBodyName"],
            "vehicles": [
                {
                    "vehicleId": "vehicle_id",
                    "name": "model_description",
                    "tags": [{"value": ""}],
                }
            ],
        }
        mock_session = Mock()
        mock_get_trim_line_codes.return_value = []
        mock_get_basic_line.return_value = create_test_line_item(
            vendor=Vendor.MERCEDES_BENZ,
            market=Market.DE,
            line_description="line_description",
        )
        model_scraper = ModelScraper(
            market=Market.DE,
            session=mock_session,
            line_item_repository=FileSystemLineItemRepository,
        )

        model_scraper.get_model(data, "version")
        mock_get_trim_line_codes.assert_called_with("vehicle_id", "version")

    @patch("src.price_monitor.price_scraper.mercedes_benz.model_scraper.logger")
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.ModelScraper._scrape_trim_line"
    )
    def test__append_trim_line_calls_logger_when_api_fails_and_could_not_load_data_from_yesterday(
        self, mock_execute_request, mock_logger
    ):
        basic_line = create_test_line_item(
            vendor=Vendor.MERCEDES_BENZ,
            market=Market.DE,
            model_code="model_code",
            model_description="MODEL_DESCRIPTION",
        )
        model_options = {
            "components": {"line_code": {"name": "trim_line_name", "selected": True}}
        }
        trim_line_codes = ["line_code"]
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_model_filter_by_line_code.return_value = []
        mock_execute_request.side_effect = HTTPError()

        model_scraper = ModelScraper(
            market=Market.DE,
            session=mock_session,
            line_item_repository=mock_line_item_repository,
        )

        model_scraper._append_trim_lines(
            basic_line, model_options, trim_line_codes, "vehicle_id", "version", ""
        )
        mock_logger.info.assert_called_with(
            "[DE] Could not Load trim line for MODEL_DESCRIPTION"
        )

    @patch("src.price_monitor.price_scraper.mercedes_benz.model_scraper.logger")
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.parse_line_options"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.model_scraper.parse_line_item"
    )
    def test_get_basic_line_returns_basic_line_item_when_api_is_successful_for_option(
        self, mock_parse_line_item, mock_parse_line_options, mock_logger
    ):
        mock_parse_line_item.return_value = create_test_line_item()
        mock_parse_line_options.side_effect = HTTPError()
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_line_option_codes_for_line_code.return_value = []
        mock_session = Mock()
        model_scraper = ModelScraper(
            market=Market.DE,
            session=mock_session,
            line_item_repository=mock_line_item_repository,
        )
        model_scraper._get_basic_line("classBodyName", {}, {}, "")
        mock_logger.error.assert_called_with(
            "[DE] Failed to scrape options for mercedes_benz, for model:  test BASIC LINE Reason: ''. "
            "Loading options from previous dataset..."
        )
        mock_logger.info.assert_called_with(
            "[DE] Loaded 0 options for mercedes_benz, for model:  test BASIC LINE."
        )
