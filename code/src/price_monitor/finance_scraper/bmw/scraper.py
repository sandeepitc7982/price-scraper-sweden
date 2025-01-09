from typing import List

import requests
from loguru import logger

from src.price_monitor.finance_scraper.bmw.finance_scraper import FinanceScraperBMWUk
from src.price_monitor.finance_scraper.finance_vendor_scraper import (
    FinanceVendorScraper,
)
from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.finance_item_repository import (
    FileSystemFinanceLineItemRepository,
)
from src.price_monitor.price_scraper.bmw.constants import X_API_KEY
from src.price_monitor.price_scraper.bmw.parser import (
    parse_ix_model_codes,
    parse_model_matrix_to_line_items,
)
from src.price_monitor.price_scraper.bmw.scraper import (
    get_ix_models,
    get_model_matrix,
    get_updated_token,
)
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


class BMWFinanceScraper(FinanceVendorScraper):
    def __init__(
        self,
        finance_line_item_repository: FileSystemFinanceLineItemRepository,
        config: dict = None,
    ):
        self.markets: list[Market] = []
        self.markets = config["finance_scraper"]["enabled"][Vendor.BMW]
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
                f"[{market}] Failed to scrape finance options for {Vendor.BMW}, {e}. Loading previous dataset..."
            )
            response.extend(
                self.finance_line_item_repository.load_market(
                    date=yesterday_dashed_str_with_key(),
                    market=market,
                    vendor=Vendor.BMW,
                )
            )
        return response

    def _scrape_finance_options_for_market(
        self, market: Market
    ) -> List[FinanceLineItem]:
        self.market = market
        self.session = requests.Session()
        self.req_header = {
            "Content-Type": "application/json",
            X_API_KEY: get_updated_token(),
        }
        response: List[FinanceLineItem] = []
        if market == Market.UK:
            finance_scraper_uk = FinanceScraperBMWUk(
                self.finance_line_item_repository, self.session, self.config
            )
            finance_scraper_uk.IX_MODELS = []
            model_matrix = get_model_matrix(self.market, self.session, self.req_header)
            parsed_line_items = parse_model_matrix_to_line_items(model_matrix, market)
            response.extend(
                finance_scraper_uk.scrape_finance_options_for_uk(
                    parsed_line_items, model_matrix
                )
            )
            bmw_i_model_matrix, bmw_i_line_items = get_ix_models(
                market, self.req_header, self.session
            )
            finance_scraper_uk.IX_MODELS = parse_ix_model_codes(bmw_i_model_matrix)
            response.extend(
                finance_scraper_uk.scrape_finance_options_for_uk(
                    bmw_i_line_items, bmw_i_model_matrix
                )
            )
        return response
