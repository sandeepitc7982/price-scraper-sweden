import unittest
from test.price_monitor.utils.test_data_builder import create_test_finance_line_item
from unittest.mock import Mock, patch

from requests import HTTPError

from src.price_monitor.finance_scraper.audi.finance_scraper_uk import (
    FinanceScraperAudiUk,
)
from src.price_monitor.finance_scraper.audi.scraper import AudiFinanceScraper
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


class TestAudiScraper(unittest.TestCase):
    @patch.object(AudiFinanceScraper, "_scrape_finance_options_for_market")
    def test_scrape_finance_options(self, mock_scrape_finance_options_for_market):
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]
        mock_finance_line_item_repository = Mock()
        config = {"finance_scraper": {"enabled": {"audi": ["UK"]}}}
        mock_scrape_finance_options_for_market.return_value = [finance_line_item]

        scraper = AudiFinanceScraper(
            finance_line_item_repository=mock_finance_line_item_repository,
            config=config,
        )

        actual_result = scraper.scrape_finance_options(Market.UK)

        assert actual_result == expected_result

    @patch.object(AudiFinanceScraper, "_scrape_finance_options_for_market")
    @patch("src.price_monitor.finance_scraper.audi.scraper.logger")
    def test_scrape_finance_options_loads_yesterdays_data_when_response_empty_list(
        self, mock_logger, mock_scrape_finance_options_for_market
    ):
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]
        mock_finance_line_item_repository = Mock()
        config = {"finance_scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        mock_scrape_finance_options_for_market.return_value = []
        mock_finance_line_item_repository.load_market.return_value = [finance_line_item]
        scraper = AudiFinanceScraper(
            finance_line_item_repository=mock_finance_line_item_repository,
            config=config,
        )

        actual_result = scraper.scrape_finance_options(Market.UK)
        assert actual_result == expected_result

        mock_finance_line_item_repository.load_market.assert_called_with(
            date=yesterday_dashed_str_with_key(), market=Market.UK, vendor=Vendor.AUDI
        )
        mock_logger.error.assert_called_with(
            "[UK] Failed to scrape finance options for audi, Something went wrong, "
            "Fetched 0 models. Loading previous dataset..."
        )

    @patch.object(AudiFinanceScraper, "_scrape_finance_options_for_market")
    @patch("src.price_monitor.finance_scraper.audi.scraper.logger")
    def test_scrape_finance_options_loads_yesterdays_data_when_it_fails(
        self, mock_logger, mock_scrape_finance_options_for_market
    ):
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]
        mock_finance_line_item_repository = Mock()
        config = {"finance_scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        mock_scrape_finance_options_for_market.side_effect = HTTPError()
        mock_finance_line_item_repository.load_market.return_value = [finance_line_item]
        scraper = AudiFinanceScraper(
            finance_line_item_repository=mock_finance_line_item_repository,
            config=config,
        )

        actual_result = scraper.scrape_finance_options(Market.UK)
        assert actual_result == expected_result

        mock_finance_line_item_repository.load_market.assert_called_with(
            date=yesterday_dashed_str_with_key(), market=Market.UK, vendor=Vendor.AUDI
        )
        mock_logger.error.assert_called_with(
            "[UK] Failed to scrape finance options for audi, . "
            "Loading previous dataset..."
        )

    @patch.object(FinanceScraperAudiUk, "scrape_finance_options_for_uk")
    def test_scrape_finance_options_for_market(
        self, mock_scrape_finance_options_for_uk
    ):
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]
        mock_finance_line_item_repository = Mock()
        mock_scrape_finance_options_for_uk.return_value = [finance_line_item]
        config = {"finance_scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}

        scraper = AudiFinanceScraper(
            finance_line_item_repository=mock_finance_line_item_repository,
            config=config,
        )

        actual_result = scraper._scrape_finance_options_for_market(Market.UK)

        assert expected_result == actual_result
