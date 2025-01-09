import unittest
from test.price_monitor.utils.test_data_builder import (
    create_test_finance_line_item,
    create_test_line_item,
)
from unittest.mock import Mock, patch

from requests import HTTPError

from src.price_monitor.finance_scraper.bmw.finance_scraper import FinanceScraperBMWUk
from src.price_monitor.finance_scraper.bmw.scraper import BMWFinanceScraper
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


class TestBMWScraper(unittest.TestCase):
    @patch.object(BMWFinanceScraper, "_scrape_finance_options_for_market")
    def test_scrape_finance_options(self, mock_scrape_finance_options_for_market):
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]
        mock_finance_line_item_repository = Mock()
        config = {"finance_scraper": {"enabled": {"bmw": ["UK"]}}}
        mock_scrape_finance_options_for_market.return_value = [finance_line_item]

        scraper = BMWFinanceScraper(
            finance_line_item_repository=mock_finance_line_item_repository,
            config=config,
        )

        actual_result = scraper.scrape_finance_options(Market.UK)

        assert actual_result == expected_result

    @patch.object(BMWFinanceScraper, "_scrape_finance_options_for_market")
    @patch("src.price_monitor.finance_scraper.bmw.scraper.logger")
    def test_scrape_finance_options_loads_yesterdays_data_when_response_empty_list(
        self, mock_logger, mock_scrape_finance_options_for_market
    ):
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]
        mock_finance_line_item_repository = Mock()
        config = {"finance_scraper": {"enabled": {Vendor.BMW: [Market.UK]}}}
        mock_scrape_finance_options_for_market.return_value = []
        mock_finance_line_item_repository.load_market.return_value = [finance_line_item]
        scraper = BMWFinanceScraper(
            finance_line_item_repository=mock_finance_line_item_repository,
            config=config,
        )

        actual_result = scraper.scrape_finance_options(Market.UK)
        assert actual_result == expected_result

        mock_finance_line_item_repository.load_market.assert_called_with(
            date=yesterday_dashed_str_with_key(), market=Market.UK, vendor=Vendor.BMW
        )
        mock_logger.error.assert_called_with(
            "[UK] Failed to scrape finance options for bmw, Something went wrong, "
            "Fetched 0 models. Loading previous dataset..."
        )

    @patch.object(BMWFinanceScraper, "_scrape_finance_options_for_market")
    @patch("src.price_monitor.finance_scraper.bmw.scraper.logger")
    def test_scrape_finance_options_loads_yesterdays_data_when_it_fails(
        self, mock_logger, mock_scrape_finance_options_for_market
    ):
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]
        mock_finance_line_item_repository = Mock()
        config = {"finance_scraper": {"enabled": {Vendor.BMW: [Market.UK]}}}
        mock_scrape_finance_options_for_market.side_effect = HTTPError()
        mock_finance_line_item_repository.load_market.return_value = [finance_line_item]
        scraper = BMWFinanceScraper(
            finance_line_item_repository=mock_finance_line_item_repository,
            config=config,
        )

        actual_result = scraper.scrape_finance_options(Market.UK)
        assert actual_result == expected_result

        mock_finance_line_item_repository.load_market.assert_called_with(
            date=yesterday_dashed_str_with_key(), market=Market.UK, vendor=Vendor.BMW
        )
        mock_logger.error.assert_called_with(
            "[UK] Failed to scrape finance options for bmw, . "
            "Loading previous dataset..."
        )

    @patch("src.price_monitor.finance_scraper.bmw.scraper.parse_ix_model_codes")
    @patch("src.price_monitor.finance_scraper.bmw.scraper.get_ix_models")
    @patch(
        "src.price_monitor.finance_scraper.bmw.scraper.parse_model_matrix_to_line_items"
    )
    @patch("src.price_monitor.finance_scraper.bmw.scraper.get_model_matrix")
    @patch.object(FinanceScraperBMWUk, "scrape_finance_options_for_uk")
    def test_scrape_finance_options_for_market(
        self,
        mock_scrape_finance_options_for_uk,
        mock_get_model_matrix,
        mock_parse_model_matrix_to_line_items,
        mock_get_ix_models,
        mock_parse_ix_model_codes,
    ):
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]
        mock_finance_line_item_repository = Mock()
        mock_get_model_matrix.return_value = {
            "I": {"modelRanges": {"models": "model_code"}}
        }
        mock_parse_model_matrix_to_line_items.return_value = [create_test_line_item()]
        mock_get_ix_models.return_value = [{"model": "matrix"}, []]
        mock_scrape_finance_options_for_uk.side_effect = [[finance_line_item], []]
        mock_parse_ix_model_codes.return_value = ["IXSA", "IXMA"]
        config = {"finance_scraper": {"enabled": {Vendor.BMW: [Market.UK]}}}

        scraper = BMWFinanceScraper(
            finance_line_item_repository=mock_finance_line_item_repository,
            config=config,
        )

        actual_result = scraper._scrape_finance_options_for_market(Market.UK)

        assert expected_result == actual_result
