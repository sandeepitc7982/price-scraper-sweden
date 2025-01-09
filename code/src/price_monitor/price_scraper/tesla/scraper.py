from typing import List, Set

import requests
from loguru import logger
from requests import HTTPError
from retry import retry

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.constants import E2E_TEST_LIST_SIZE
from src.price_monitor.price_scraper.tesla.constants import BASE_URL, MARKET_MAP
from src.price_monitor.price_scraper.tesla.parser import (
    adjust_otr_price,
    parse_available_models_links,
    parse_line_items,
    parse_model_and_series,
)
from src.price_monitor.price_scraper.tesla.scrape_otr import get_otr_prices_for_model
from src.price_monitor.price_scraper.vendor_scraper import VendorScraper
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key
from src.price_monitor.utils.selenium_caller import selenium_execute_request


def _find_available_models(market: Market) -> Set[str]:
    model_links_json: dict = {}
    try:
        url = f"{BASE_URL}/{MARKET_MAP.get(market)}/api/tesla/header/megamenu/v1_2"
        model_links_json = selenium_execute_request(url=url, response_format="json")
        return parse_available_models_links(model_links_json)
    except Exception as e:
        logger.error(
            f"[{market}] Failed to parse available models from response: {model_links_json}",
            e,
        )
        raise e


class TeslaScraper(VendorScraper):
    def __init__(self, line_item_repository, config: dict = None):
        self.markets: list[Market] = []
        self.line_item_repository = line_item_repository
        self.config = config
        self.markets = config["scraper"]["enabled"][Vendor.TESLA]

    def run_tesla(self) -> List[LineItem]:
        response: List[LineItem] = []

        for market in self.markets:
            response.extend(self.scrape_models(market))

        return response

    def scrape_models(self, market) -> List[LineItem]:
        response: List[LineItem] = []

        try:
            models = self._scrape_models_for_market(market=market)
            if len(models) == 0:
                raise ValueError("Something went wrong, Fetched 0 models")
            response.extend(models)
        except Exception as e:
            self.get_yesterdays_data(response, market, e)

        return response

    def get_yesterdays_data(self, response, market, e):
        logger.exception(
            f"[{market}] Failed to scrape models for {Vendor.TESLA}, {e}. Loading previous dataset..."
        )
        self._extend_response_with_yesterdays_data(response, market)

    def _extend_response_with_yesterdays_data(self, response, market):
        response.extend(
            self.line_item_repository.load_market(
                date=yesterday_dashed_str_with_key(),
                market=market,
                vendor=Vendor.TESLA,
            )
        )

    @retry(tries=5, delay=1, backoff=2)
    def _scrape_models_for_market(self, market: Market) -> List[LineItem]:
        response: List[LineItem] = []

        # This method is not thread safe since the market and session variables are shared.
        self.session = requests.session()
        self.market = market
        self.headers = {
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            ",application/signed-exchange;v=b3;q=0.7",
        }

        models = _find_available_models(market)

        if self.config.get("e2e_tests"):
            models = list(models)[:E2E_TEST_LIST_SIZE]

        for model in models:
            logger.debug(f"[{market}] Scraping {model}")
            response.extend(self._scrape_model(model))

        logger.info(f"Scraped {len(response)} models for market {market}")
        return response

    def _scrape_model(self, model: str) -> List[LineItem]:
        url = f"{BASE_URL}{model}#overview"
        try:
            model_page = selenium_execute_request(url=url, response_format="text")
            line_items = parse_line_items(model_page, self.market)
            if self.market == Market.UK:
                otr_prices = get_otr_prices_for_model(url)
                line_items = adjust_otr_price(line_items, otr_prices)
            return line_items
        except HTTPError as e:
            model, series = parse_model_and_series(model, self.market)
            logger.error(
                f"[{self.market}] Failed to scrape {model} for {Vendor.TESLA}, reason: {e}. Loading previous dataset..."
            )
            return self.line_item_repository.load_model_filter_by_series(
                date=yesterday_dashed_str_with_key(),
                market=self.market,
                vendor=Vendor.TESLA,
                series=series,
            )
