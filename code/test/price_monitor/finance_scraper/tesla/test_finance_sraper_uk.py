import unittest
from pathlib import Path
from test.price_monitor.utils.test_data_builder import (
    create_test_finance_line_item,
    create_test_line_item,
)
from unittest.mock import Mock, patch

from requests import HTTPError

from src.price_monitor.finance_scraper.tesla.finance_scraper import (
    FinanceScraperTeslaUk,
)
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.utils.clock import (
    today_dashed_str,
    yesterday_dashed_str_with_key,
)

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"


class TestFinanceScraper(unittest.TestCase):
    @patch.object(FinanceScraperTeslaUk, "scrape_finance_option_for_model")
    @patch(
        "src.price_monitor.finance_scraper.tesla.finance_scraper._find_available_models"
    )
    def test_scrape_finance_options_for_uk(
        self, mock__find_available_models, mock_scrape_finance_option_for_model
    ):
        finance_line_item = create_test_finance_line_item(
            vendor=Vendor.TESLA,
            series="Z",
            model_range_code="G29",
            model_range_description="TESLA Z4",
            model_code="HF51",
            model_description="TESLA Z4 M40i - automatic",
            line_code="M_PERFORMANCE_LINE",
            line_description="M_PERFORMANCE_LINE",
            contract_type="PCP",
            monthly_rental_nlp=410.83,
            monthly_rental_glp=493.0,
            market=Market.UK,
        )

        mock__find_available_models.return_value = ["model1"]
        mock_scrape_finance_option_for_model.return_value = [finance_line_item]

        config = {"scraper": {"enabled": {Vendor.TESLA: [Market.UK]}}}

        mock_session = Mock()

        tesla_finance_scraper = FinanceScraperTeslaUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )

        actual_finance_line_items = (
            tesla_finance_scraper.scrape_finance_options_for_uk()
        )
        mock__find_available_models.assert_called_with(market=Market.UK)
        assert actual_finance_line_items[0].asdict() == finance_line_item.asdict()

    @patch(
        "src.price_monitor.finance_scraper.tesla.finance_scraper.parse_finance_line_items"
    )
    @patch(
        "src.price_monitor.finance_scraper.tesla.finance_scraper.get_finance_details_for_model"
    )
    @patch("src.price_monitor.finance_scraper.tesla.finance_scraper.parse_line_items")
    @patch(
        "src.price_monitor.finance_scraper.tesla.finance_scraper.selenium_execute_request"
    )
    def test_scrape_finance_option_for_model(
        self,
        mock_selenium_execute_request,
        mock_parse_line_items,
        mock_get_finance_details_for_model,
        mock_parse_finance_line_items,
    ):
        finance_line_item = create_test_finance_line_item(
            vendor=Vendor.TESLA,
            series="Z",
            model_range_code="G29",
            model_range_description="TESLA Z4",
            model_code="HF51",
            model_description="TESLA Z4 M40i - automatic",
            line_code="M_PERFORMANCE_LINE",
            line_description="M_PERFORMANCE_LINE",
            contract_type="PCP",
            monthly_rental_nlp=410.83,
            monthly_rental_glp=493.0,
            market=Market.UK,
        )

        mock_parse_line_items.return_value = [
            create_test_line_item(
                recorded_at=today_dashed_str(),
                vendor=Vendor.TESLA,
                market=Market.UK,
            ),
        ]
        mock_selenium_execute_request.return_value = "model_text"
        mock_parse_line_items.return_value = ["model1"]
        mock_get_finance_details_for_model.return_value = {"model": {"PCP": 1000}}
        mock_parse_finance_line_items.return_value = [finance_line_item]

        config = {"scraper": {"enabled": {Vendor.TESLA: [Market.UK]}}}

        mock_session = Mock()

        tesla_finance_scraper = FinanceScraperTeslaUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )

        actual_finance_line_items = (
            tesla_finance_scraper.scrape_finance_option_for_model("model_1")
        )

        mock_selenium_execute_request.assert_called_with(
            url="https://www.tesla.commodel_1#overview", response_format="text"
        )
        mock_parse_line_items.assert_called_with("model_text", Market.UK)
        mock_get_finance_details_for_model.assert_called_with(
            "https://www.tesla.commodel_1#overview"
        )
        mock_parse_finance_line_items.assert_called_with(
            ["model1"], {"model": {"PCP": 1000}}
        )
        assert actual_finance_line_items[0].asdict() == finance_line_item.asdict()

    @patch(
        "src.price_monitor.finance_scraper.tesla.finance_scraper.parse_model_and_series"
    )
    @patch(
        "src.price_monitor.finance_scraper.tesla.finance_scraper.selenium_execute_request"
    )
    def test_scrape_finance_option_for_model_when_scraping_fail_load_previous_data(
        self, mock_selenium_execute_request, mock_parse_model_and_series
    ):
        finance_line_item = create_test_finance_line_item(
            vendor=Vendor.TESLA,
            series="Z",
            model_range_code="G29",
            model_range_description="TESLA Z4",
            model_code="HF51",
            model_description="TESLA Z4 M40i - automatic",
            line_code="M_PERFORMANCE_LINE",
            line_description="M_PERFORMANCE_LINE",
            contract_type="PCP",
            monthly_rental_nlp=410.83,
            monthly_rental_glp=493.0,
            market=Market.UK,
        )

        mock_repository = Mock()
        mock_repository.load_model_filter_by_series.return_value = [finance_line_item]
        mock_parse_model_and_series.return_value = ["model_1", "series1"]
        mock_selenium_execute_request.side_effect = HTTPError()

        config = {"scraper": {"enabled": {Vendor.TESLA: [Market.UK]}}}

        mock_session = Mock()

        tesla_finance_scraper = FinanceScraperTeslaUk(
            finance_line_item_repository=mock_repository,
            config=config,
            session=mock_session,
        )

        actual_finance_line_items = (
            tesla_finance_scraper.scrape_finance_option_for_model("model_1")
        )

        mock_selenium_execute_request.assert_called_with(
            url="https://www.tesla.commodel_1#overview", response_format="text"
        )
        mock_repository.load_model_filter_by_series.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.UK,
            vendor=Vendor.TESLA,
            series="series1",
        )
        assert actual_finance_line_items[0].asdict() == finance_line_item.asdict()
