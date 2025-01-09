from typing import List

import requests
from loguru import logger
from requests import Session
from retry import retry

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.constants import E2E_TEST_LIST_SIZE
from src.price_monitor.price_scraper.mercedes_benz.constants import (
    BASE_URL,
    MARKET_MAP_BASE_URL,
    MARKET_MAP_MODEL_SERIES_URL,
    MODEL_SERIES_URL,
)
from src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa import (
    MercedesBenzUSAScraper,
)
from src.price_monitor.price_scraper.mercedes_benz.model_scraper import ModelScraper
from src.price_monitor.price_scraper.mercedes_benz.parser import (
    build_model_range_description,
    parse_available_models_links,
)
from src.price_monitor.price_scraper.vendor_scraper import VendorScraper
from src.price_monitor.utils.caller import execute_request
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


# get all model end points that helps to scrape the respective trim lines.
def _find_available_models(market: Market, session: Session) -> set[str]:
    try:
        model_links_json = execute_request(
            "get", f"{BASE_URL}{MARKET_MAP_BASE_URL.get(market)}", session
        )
        return parse_available_models_links(model_links_json)
    except Exception as e:
        logger.error(
            f"[{market}] Failed to parse available models because of exception : {e}"
        )
        raise e


class MercedesBenzScraper(VendorScraper):
    def __init__(self, line_item_repository, config: dict = None):
        self.markets: list[Market] = []
        self.line_item_repository = line_item_repository
        self.config = config
        self.markets = config["scraper"]["enabled"][Vendor.MERCEDES_BENZ]

    # scrape all models for building trim line end point.
    def scrape_models(self, market: Market) -> List[LineItem]:
        response: List[LineItem] = []
        try:
            models = self._scrape_models_for_market(market=market)
            if len(models) == 0:
                raise ValueError("Something went wrong, Fetched 0 models")
            response.extend(models)
        except Exception as e:
            logger.exception(
                f"[{market}] Failed to scrape models for {Vendor.MERCEDES_BENZ}, {e}. Loading previous dataset..."
            )

            yesterdays_data = self.line_item_repository.load_market(
                date=yesterday_dashed_str_with_key(),
                market=market,
                vendor=Vendor.MERCEDES_BENZ,
            )
            response.extend(yesterdays_data)
        return response

    # scrape the models from the end point and collect trim line information
    @retry(tries=5, delay=1, backoff=2)
    def _scrape_models_for_market(self, market: Market) -> List[LineItem]:
        response: List[LineItem] = []
        # This method is not thread safe since the market and session variables are shared.
        self.session = requests.session()
        self.market = market
        if market == Market.US:
            mercedes_benz_usa_scraper = MercedesBenzUSAScraper(
                line_item_repository=self.line_item_repository,
                session=self.session,
                config=self.config,
            )
            return mercedes_benz_usa_scraper.scrape_models()

        self.model_scraper = ModelScraper(
            self.market, self.session, self.line_item_repository, self.config
        )
        version = self._scrape_updated_version()
        models = _find_available_models(market, self.session)

        if self.config.get("e2e_tests"):
            models = list(models)[:E2E_TEST_LIST_SIZE]

        for model in models:
            logger.debug(f"[{market}] Scraping {model}")
            line_items = self._scrape_model(model, version)
            response.extend(line_items)
        logger.info(f"Scraped {len(response)} models for market {market}")
        return response

    def _scrape_updated_version(self) -> str:
        url = f"{MODEL_SERIES_URL}{MARKET_MAP_MODEL_SERIES_URL.get(self.market)}/CCci/version"
        data = execute_request("get", url, self.session)
        return data["dataVersion"]

    def _scrape_model(self, model: str, version: str) -> List[LineItem]:
        url = (
            f"{MODEL_SERIES_URL}{MARKET_MAP_MODEL_SERIES_URL.get(self.market)}/CCci/{version}/motorizations/model/"
            f"{model}"
        )
        try:
            model_page_json = execute_request("get", url, self.session)
            return self.model_scraper.get_model(model_page_json, version)
        except Exception as e:
            logger.error(
                f"[{self.market}] Failed to scrape {model} for {Vendor.MERCEDES_BENZ}, reason: {e}. Loading previous dataset..."
            )
            line_items = (
                self.line_item_repository.load_model_filter_by_model_range_description(
                    date=yesterday_dashed_str_with_key(),
                    market=self.market,
                    vendor=Vendor.MERCEDES_BENZ,
                    model_range_description=build_model_range_description(model),
                )
            )
            logger.info(f"Loaded {len(line_items)} lines for {model}")
            return line_items
