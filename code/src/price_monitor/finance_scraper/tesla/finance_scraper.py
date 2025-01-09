from typing import List

from loguru import logger

from src.price_monitor.finance_scraper.tesla.constants import BASE_URL
from src.price_monitor.finance_scraper.tesla.finance_parser import (
    parse_finance_line_items,
)
from src.price_monitor.finance_scraper.tesla.selenium import (
    get_finance_details_for_model,
)
from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.finance_item_repository import (
    FileSystemFinanceLineItemRepository,
)
from src.price_monitor.price_scraper.tesla.parser import (
    parse_line_items,
    parse_model_and_series,
)
from src.price_monitor.price_scraper.tesla.scraper import _find_available_models
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key
from src.price_monitor.utils.selenium_caller import selenium_execute_request


class FinanceScraperTeslaUk:
    def __init__(
        self,
        finance_line_item_repository: FileSystemFinanceLineItemRepository,
        session,
        config,
    ):
        self.finance_line_item_repository = finance_line_item_repository
        self.config = config
        self.market = Market.UK
        self.session = session
        self.vendor = Vendor.TESLA

    def scrape_finance_options_for_uk(self):
        response = []

        models = _find_available_models(market=Market.UK)

        if self.config.get("e2e_tests"):
            models = models[:1]

        for model in models:
            logger.debug(f"Fetching finance options for model {model}")
            finance_line_items = self.scrape_finance_option_for_model(model)
            response.extend(finance_line_items)

        logger.info(f"[UK] scraped {len(response)} Finance Items for Tesla")
        return response

    def scrape_finance_option_for_model(self, model: str) -> List[FinanceLineItem]:
        response = []
        url = f"{BASE_URL}{model}#overview"
        try:
            model_page = selenium_execute_request(url=url, response_format="text")
            line_items = parse_line_items(model_page, self.market)
            finance_line_details = get_finance_details_for_model(url)
            response = parse_finance_line_items(line_items, finance_line_details)

        except Exception as e:
            model, series = parse_model_and_series(model, Market.UK)
            logger.error(
                f"[{Market.UK}] Failed to scrape {model} for {Vendor.TESLA}, reason: {e}. Loading previous dataset..."
            )
            response = self.finance_line_item_repository.load_model_filter_by_series(
                date=yesterday_dashed_str_with_key(),
                market=self.market,
                vendor=Vendor.TESLA,
                series=series,
            )
        return response
