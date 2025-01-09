import unittest
from test.price_monitor.utils.test_data_builder import create_test_line_item
from unittest.mock import Mock, patch

from requests import HTTPError

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.price_scraper.tesla.scraper import TeslaScraper
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


class TestTeslaScraper(unittest.TestCase):
    scraper_config = {"scraper": {"enabled": {Vendor.TESLA: [Market.DE]}}}
    headers = {
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    }

    @patch("src.price_monitor.price_scraper.tesla.scraper.TeslaScraper.scrape_models")
    def test_run_tesla_when_given_markets_then_run_scraper_in_series(
        self, mock_scrape_models
    ):
        expected_result = [
            create_test_line_item(
                model_description="MX3", vendor=Vendor.TESLA, market="DE"
            ),
            create_test_line_item(
                model_description="MY3", vendor=Vendor.TESLA, market="US"
            ),
        ]

        tesla_scraper = TeslaScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )

        setattr(tesla_scraper, "markets", [Market.DE, Market.US])

        mock_scrape_models.side_effect = [
            [
                create_test_line_item(
                    model_description="MX3", vendor=Vendor.TESLA, market="DE"
                )
            ],
            [
                create_test_line_item(
                    model_description="MY3", vendor=Vendor.TESLA, market="US"
                )
            ],
        ]

        actual_line_item = tesla_scraper.run_tesla()

        assert expected_result == actual_line_item

    @patch("src.price_monitor.price_scraper.tesla.scraper.get_otr_prices_for_model")
    @patch("src.price_monitor.price_scraper.tesla.scraper.parse_line_items")
    @patch("src.price_monitor.price_scraper.tesla.scraper.selenium_execute_request")
    def test__scrape_model_calls_parser_with_model_page_from_the_url_call(
        self, mock_execute_request, mock_parse_line_items, mock_get_otr_prices_for_model
    ):
        # ASSEMBLE
        expected_scraped_model = [create_test_line_item(series="Tesla_best_series")]
        mock_parse_line_items.return_value = expected_scraped_model

        mock_execute_request.return_value = "Model Tesla Best You've Ever Seen"
        mock_get_otr_prices_for_model.return_value = {}

        tesla_scraper = TeslaScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        setattr(tesla_scraper, "session", Mock())
        setattr(tesla_scraper, "market", Market.DE)
        setattr(tesla_scraper, "headers", self.headers)

        # ACT
        actual_scraped_model = tesla_scraper._scrape_model("model_a")

        # ASSERT
        mock_parse_line_items.assert_called_with(
            "Model Tesla Best You've Ever Seen", Market.DE
        )
        assert actual_scraped_model == expected_scraped_model

    @patch(
        "src.price_monitor.price_scraper.tesla.scraper.parse_line_items",
        return_value=[create_test_line_item(series="Tesla_best_series")],
    )
    @patch("src.price_monitor.price_scraper.tesla.scraper.get_otr_prices_for_model")
    @patch("src.price_monitor.price_scraper.tesla.scraper.selenium_execute_request")
    def test__scrape_model_calls_url_with_the_model(
        self, mock_execute_request, mock_parse_line_items, mock_get_otr_prices_for_model
    ):
        # ASSEMBLE
        mock_session = Mock()
        mock_execute_request.return_value = "Model Tesla Best You've Ever Seen"
        mock_get_otr_prices_for_model.return_value = {}

        tesla_scraper = TeslaScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        setattr(tesla_scraper, "session", mock_session)
        setattr(tesla_scraper, "market", Market.DE)
        setattr(tesla_scraper, "headers", self.headers)

        # ACT
        model_tesla = "best_model_tesla"
        tesla_scraper._scrape_model(model_tesla)

        expected_url_call = f"https://www.tesla.com{model_tesla}#overview"

        # ASSERT
        mock_execute_request.assert_called_with(
            url=expected_url_call, response_format="text"
        )

    @patch(
        "src.price_monitor.price_scraper.tesla.scraper._find_available_models",
        return_value=["model_a"],
    )
    @patch(
        "src.price_monitor.price_scraper.tesla.scraper.TeslaScraper._scrape_model",
        return_value=[create_test_line_item(model_code="model_a")],
    )
    def test__scrape_models_for_market_returns_line_items_from_all_markets(
        self, mock_available_models, mock_scrape_model
    ):
        tesla_scraper = TeslaScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )

        actual_scraped_model = tesla_scraper._scrape_models_for_market(Market.DE)

        assert actual_scraped_model == [create_test_line_item(model_code="model_a")]

    @patch(
        "src.price_monitor.price_scraper.tesla.scraper._find_available_models",
        return_value=[],
    )
    @patch(
        "src.price_monitor.price_scraper.tesla.scraper.TeslaScraper._scrape_model",
        return_value=[create_test_line_item(model_code="model_a")],
    )
    def test__scrape_models_for_market_returns_an_empty_list_when_find_available_markets_is_empty(
        self, mock_available_models, mock_scrape_model
    ):
        tesla_scraper = TeslaScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )

        actual_scraped_model = tesla_scraper._scrape_models_for_market(Market.DE)

        assert actual_scraped_model == []

    @patch(
        "src.price_monitor.price_scraper.tesla.scraper.TeslaScraper._scrape_models_for_market"
    )
    def test_scrape_models_returns_yesterdays_all_models_if__scrape_models_for_market_returns_empty_list(
        self, mock_scrape_models_for_market
    ):
        mock_scrape_models_for_market.return_value = []

        mock_line_item_repository = Mock()
        mock_line_item_repository.load_market.return_value = []

        tesla_scraper = TeslaScraper(
            mock_line_item_repository,
            self.scraper_config,
        )

        tesla_scraper.scrape_models(Market.DE)

        mock_line_item_repository.load_market.assert_called_with(
            date=yesterday_dashed_str_with_key(), market=Market.DE, vendor=Vendor.TESLA
        )

    @patch("src.price_monitor.price_scraper.tesla.scraper.get_otr_prices_for_model")
    @patch("src.price_monitor.price_scraper.tesla.scraper.selenium_execute_request")
    def test__scrape_model_gets_model_name_from_market_model_combination_for_us_market(
        self, mock_execute_request, mock_get_otr_prices_for_model
    ):
        mock_execute_request.side_effect = HTTPError()
        mock_session = Mock()

        mock_line_item_repository = Mock()
        mock_line_item_repository.load_market.return_value = []
        mock_get_otr_prices_for_model.return_value = {}

        tesla_scraper = TeslaScraper(
            mock_line_item_repository,
            self.scraper_config,
        )
        setattr(tesla_scraper, "session", mock_session)
        setattr(tesla_scraper, "market", Market.US)
        setattr(tesla_scraper, "headers", self.headers)

        model = "/modelx"
        tesla_scraper._scrape_model(model)

        mock_line_item_repository.load_model_filter_by_series.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.TESLA,
            series="mx",
        )

    @patch("src.price_monitor.price_scraper.tesla.scraper.get_otr_prices_for_model")
    @patch("src.price_monitor.price_scraper.tesla.scraper.selenium_execute_request")
    def test__scrape_model_gets_model_name_from_market_model_combination_for_rest_of_the_markets(
        self, mock_execute_request, mock_get_otr_prices_for_model
    ):
        mock_execute_request.side_effect = HTTPError()
        mock_session = Mock()

        mock_line_item_repository = Mock()
        mock_line_item_repository.load_market.return_value = []
        mock_get_otr_prices_for_model.return_value = {}

        tesla_scraper = TeslaScraper(
            mock_line_item_repository,
            self.scraper_config,
        )
        setattr(tesla_scraper, "session", mock_session)
        setattr(tesla_scraper, "market", Market.DE)
        setattr(tesla_scraper, "headers", self.headers)

        model = "/de_da/modelx"
        tesla_scraper._scrape_model(model)

        mock_line_item_repository.load_model_filter_by_series.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.TESLA,
            series="mx",
        )

    @patch("src.price_monitor.price_scraper.tesla.scraper.get_otr_prices_for_model")
    @patch("src.price_monitor.price_scraper.tesla.scraper.parse_line_items")
    @patch("src.price_monitor.price_scraper.tesla.scraper.selenium_execute_request")
    def test__scrape_model_should_scrape_otr_prices(
        self, mock_execute_request, mock_parse_line_items, mock_get_otr_prices_for_model
    ):
        # ASSEMBLE
        expected_scraped_model = create_test_line_item(
            series="Tesla_best_series", line_code="mxt3", on_the_road_price=325
        )
        mock_parse_line_items.return_value = [
            create_test_line_item(series="Tesla_best_series", line_code="mxt3")
        ]

        mock_execute_request.return_value = "Model Tesla Best You've Ever Seen"
        mock_get_otr_prices_for_model.return_value = {"mxt3": "$325"}

        tesla_scraper = TeslaScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        setattr(tesla_scraper, "session", Mock())
        setattr(tesla_scraper, "market", Market.UK)
        setattr(tesla_scraper, "headers", self.headers)

        # ACT
        actual_scraped_model = tesla_scraper._scrape_model("model_a")[0]

        # ASSERT
        mock_get_otr_prices_for_model.assert_called_with(
            "https://www.tesla.commodel_a#overview"
        )
        assert actual_scraped_model == expected_scraped_model
