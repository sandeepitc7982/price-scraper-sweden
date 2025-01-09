from typing import List

import requests
from loguru import logger

from src.price_monitor.finance_scraper.audi.finance_scraper_uk import (
    FinanceScraperAudiUk,
)
from src.price_monitor.finance_scraper.finance_vendor_scraper import (
    FinanceVendorScraper,
)
from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.finance_item_repository import (
    FileSystemFinanceLineItemRepository,
)
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


class AudiFinanceScraper(FinanceVendorScraper):
    def __init__(
        self,
        finance_line_item_repository: FileSystemFinanceLineItemRepository,
        config: dict = None,
    ):
        self.markets: list[Market] = []
        self.markets = config["finance_scraper"]["enabled"][Vendor.AUDI]
        self.config = config
        self.finance_line_item_repository = finance_line_item_repository

    def scrape_finance_options(self, market: Market) -> List[FinanceLineItem]:
        response: List[FinanceLineItem] = []
        try:
            finance_line_item = self._scrape_finance_options_for_market(market)
            if len(finance_line_item) == 0:
                raise ValueError("Something went wrong, Fetched 0 models")
            response.extend(finance_line_item)
        except Exception as e:
            logger.error(
                f"[{market}] Failed to scrape finance options for {Vendor.AUDI}, {e}. Loading previous dataset..."
            )
            response.extend(
                self.finance_line_item_repository.load_market(
                    date=yesterday_dashed_str_with_key(),
                    market=market,
                    vendor=Vendor.AUDI,
                )
            )
        return response

    def _scrape_finance_options_for_market(
        self, market: Market
    ) -> List[FinanceLineItem]:
        self.session = requests.Session()
        self.market = market
        response: List[FinanceLineItem] = []
        if market == Market.UK:
            finance_scraper_uk = FinanceScraperAudiUk(
                finance_line_item_repository=self.finance_line_item_repository,
                session=self.session,
                config=self.config,
            )
            response.extend(finance_scraper_uk.scrape_finance_options_for_uk())
        return response
