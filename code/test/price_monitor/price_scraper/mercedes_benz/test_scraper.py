import unittest
from test.price_monitor.utils.test_data_builder import create_test_line_item
from unittest.mock import Mock, patch

from requests import HTTPError

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.price_scraper.mercedes_benz.model_scraper import ModelScraper
from src.price_monitor.price_scraper.mercedes_benz.scraper import MercedesBenzScraper
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


class TestMBScraper(unittest.TestCase):
    scraper_config = {
        "scraper": {"enabled": {Vendor.MERCEDES_BENZ: [Market.DE]}},
        "feature_toggle": {"is_type_hierarchy_enabled_MB": True},
    }

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.scraper.MercedesBenzScraper._scrape_models_for_market"
    )
    def test_scrape_models_loads_yesterdays_data_when_scrape_models_for_market_returns_empty_list_of_models(
        self, mock_scrape_models_for_market
    ):
        mock_scrape_models_for_market.return_value = []
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_market.return_value = [
            create_test_line_item(),
            create_test_line_item(),
        ]

        mb_scraper = MercedesBenzScraper(
            mock_line_item_repository,
            self.scraper_config,
        )
        mb_scraper.scrape_models(Market.DE)

        mock_line_item_repository.load_market.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.scraper.ModelScraper.get_model"
    )
    def test__scrape_model_calls_get_model_with_model_page_from_the_url_call_when_api_is_successful(
        self, mock_get_model
    ):
        # ASSEMBLE
        expected_scraped_model = [
            create_test_line_item(series="Mercedes_Benz_best_series")
        ]
        mock_get_model.return_value = expected_scraped_model

        mock_session = Mock()
        data = mock_session.get.return_value = Mock(
            text="Model Mercedes Best You've Ever Seen"
        )
        data = data.json()

        mb_scraper = MercedesBenzScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        setattr(mb_scraper, "session", mock_session)
        setattr(mb_scraper, "market", Market.DE)
        setattr(
            mb_scraper,
            "model_scraper",
            ModelScraper(Market.DE, mock_session, FileSystemLineItemRepository),
        )

        # ACT
        actual_scraped_model = mb_scraper._scrape_model("A-KLASSE/OFFROADER", "version")

        # ASSERT
        mock_get_model.assert_called_with(data, "version")
        assert actual_scraped_model == expected_scraped_model

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.scraper.ModelScraper.get_model"
    )
    def test__scrape_model_loads_yesterdays_data_when_api_fails(
        self, mock_execute_request
    ):
        # ASSEMBLE
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_model_filter_by_model_range_description.return_value = (
            []
        )

        mock_execute_request.side_effect = HTTPError()
        mock_session = Mock()
        mb_scraper = MercedesBenzScraper(
            mock_line_item_repository,
            self.scraper_config,
        )
        setattr(mb_scraper, "session", mock_session)
        setattr(mb_scraper, "market", Market.DE)

        # ACT
        mb_scraper._scrape_model("A-KLASSE/OFFROADER", "version")

        # ASSERT
        mock_line_item_repository.load_model_filter_by_model_range_description.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.MERCEDES_BENZ,
            model_range_description="A-KLASSE OFFROADER",
        )

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.scraper._find_available_models",
        return_value=["model_a"],
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.scraper.MercedesBenzScraper._scrape_model",
        return_value=[create_test_line_item(model_code="model_a")],
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.scraper.MercedesBenzScraper._scrape_updated_version",
        return_value=[5.2],
    )
    def test__scrape_models_for_market_returns_line_items_from_all_markets(
        self, mock__scrape_updated_version, mock_available_models, mock_scrape_model
    ):
        mb_scraper = MercedesBenzScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )

        actual_scraped_model = mb_scraper._scrape_models_for_market(Market.DE)

        assert actual_scraped_model == [create_test_line_item(model_code="model_a")]

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.scraper._find_available_models",
        return_value=[],
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.scraper.MercedesBenzScraper._scrape_model",
        return_value=[create_test_line_item(model_code="model_a")],
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.scraper.MercedesBenzScraper._scrape_updated_version",
        return_value=[5.2],
    )
    def test__scrape_models_for_market_returns_an_empty_list_when_find_available_markets_is_empty(
        self, mock__scrape_updated_version, mock_available_models, mock_scrape_model
    ):
        mb_scraper = MercedesBenzScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )

        actual_scraped_model = mb_scraper._scrape_models_for_market(Market.DE)

        assert actual_scraped_model == []
