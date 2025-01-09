from concurrent.futures import Future, ThreadPoolExecutor
from typing import List

import requests
from loguru import logger
from requests import Session

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.price_scraper.audi.constants import (
    AUDI_BASE_URL,
    AUDI_MARKET_MAP,
    DE_CONFIG_URL,
)
from src.price_monitor.price_scraper.audi.parser import (
    parse_available_model_links,
    parse_line_item_options_for_trimline,
    parse_model_line_item,
    parse_options_type,
    replace_options_type,
)
from src.price_monitor.price_scraper.audi.scraper_graphql import get_option_type_details
from src.price_monitor.price_scraper.audi.scraper_uk import AudiScraperUK
from src.price_monitor.price_scraper.audi.scraper_usa import AudiScraperUSA
from src.price_monitor.price_scraper.vendor_scraper import VendorScraper
from src.price_monitor.utils.caller import execute_request
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


def _find_available_models_link(session: Session, market: str) -> tuple[list, list]:
    url = f"{AUDI_BASE_URL}/{AUDI_MARKET_MAP[market]}/brand/{AUDI_MARKET_MAP[market]}/neuwagen.html"
    model_homepage = execute_request("get", url, session, response_format="text")
    return parse_available_model_links(model_homepage)


class AudiScraper(VendorScraper):
    def __init__(
        self,
        line_item_repository: FileSystemLineItemRepository,
        config: dict = None,
    ):
        self.markets: list[Market] = []
        self.line_item_repository = line_item_repository
        self.config = config
        self.markets = config["scraper"]["enabled"][Vendor.AUDI]

    def scrape_models(self, market: Market):
        response: List[LineItem] = []
        try:
            models = self._scrape_models_for_market(market=market)
            if len(models) == 0:
                raise ValueError("Something went wrong, Fetched 0 models")
            response.extend(models)
        except Exception as e:
            logger.exception(
                f"[{market}] Failed to scrape models for {Vendor.AUDI}, {e}. Loading previous dataset..."
            )
            response.extend(
                self.line_item_repository.load_market(
                    date=yesterday_dashed_str_with_key(),
                    market=market,
                    vendor=Vendor.AUDI,
                )
            )
        return response

    def _scrape_models_for_market(self, market: Market):
        # This method is not thread safe since the market and session variables are shared.
        self.market = market
        self.session = requests.Session()

        response: List[LineItem] = []
        if market == Market.US:
            scraper = AudiScraperUSA(
                self.line_item_repository, self.session, self.config
            )
            return [scraper.scrape_models_for_usa()]
        elif market == Market.UK:
            scraper = AudiScraperUK(
                self.line_item_repository,
                self.session,
                self.config,
            )
            response.extend(scraper.scrape_models_for_uk())
            return response

        links_having_price, link_not_having_price = _find_available_models_link(
            self.session, market
        )
        self.link_not_having_price = link_not_having_price

        if self.config.get("e2e_tests"):
            links_having_price = links_having_price[:2]

        jobs: List[Future] = []
        with ThreadPoolExecutor(
            thread_name_prefix="audi_scraper", max_workers=len(links_having_price)
        ) as ex:
            for model_link in links_having_price:
                logger.debug(f"[{market}] Scraping model {model_link}")
                scraped_line_job = ex.submit(self._scrape_models_from_link, model_link)
                jobs.append(scraped_line_job)

        for job in jobs:
            line_item = job.result()
            if line_item is not None:
                response.extend(job.result())

        for model_link in link_not_having_price:
            line_items = self._scrape_models_from_link(model_link)
            response.extend(line_items)

        logger.info(f"Scraped {len(response)} models for market {market}")
        return response

    def _scrape_models_from_link(self, model_link: str) -> List[LineItem]:
        logger.trace(f"[{self.market}] Scraping default model {model_link}")

        carinfo_link = f"{AUDI_BASE_URL}{model_link}.carinfo.mv-0-1733.31.json"
        trimlines_link = f"{AUDI_BASE_URL}{model_link}.modelsinfo.mv-0-1733.31.json"

        response = self._scrape_line_items(carinfo_link, model_link, trimlines_link)
        return response

    def _scrape_line_items(self, carinfo_link, model_link, trimlines_link):
        response: List[LineItem] = []
        try:
            trimlines_info = execute_request("get", trimlines_link, self.session)
            carinfo = execute_request("get", carinfo_link, self.session)

            model_code = carinfo["configuration"]["model"]

            params = "%7C".join(carinfo["configuration"]["items"])

            trimlines = trimlines_info["models"]

            for trimline_code, trimline_details in trimlines.items():
                line_item = self._get_line_item_from_trim_line(
                    model_link,
                    model_code,
                    trimline_code,
                    params,
                    carinfo,
                )
                if line_item is not None:
                    response.append(line_item)
        except Exception as e:
            if model_link not in self.link_not_having_price:
                logger.error(
                    f"[{self.market}] Unable to scrape model {model_link} for configuration {carinfo}, {e}"
                )
            response = self._load_trim_lines_from_previous_day(model_link)
        return response

    def _load_trim_lines_from_previous_day(self, model_link):
        logger.info(
            f"[{self.market}] Loading models from previous dataset for model_link {model_link}"
        )
        series, model_range_code = model_link.split("/")[5:7]
        response = self.line_item_repository.load_model_filter_by_model_range_code(
            date=yesterday_dashed_str_with_key(),
            market=self.market,
            vendor=Vendor.AUDI,
            series=series,
            model_range_code=model_range_code,
        )
        logger.info(
            f"[{self.market}] Load {len(response)} models for model link {model_link}"
        )
        return response

    def _get_line_item_from_trim_line(
        self,
        model_link: str,
        model_code: str,
        trimline_code: str,
        params: str,
        carinfo: dict,
    ):
        try:
            trimline_json = self._get_trim_line_json(model_code, trimline_code, params)
            line_item = parse_model_line_item(
                model_link=model_link,
                model_code=model_code,
                model_configuration=trimline_json,
                market=self.market,
            )
            line_item.line_option_codes = self.get_line_option_codes(
                model_link=model_link,
                trimline_code=trimline_code,
                trimline_details=trimline_json,
                carinfo=carinfo,
            )
            logger.debug(
                f"[{self.market}] Fetched {len(line_item.line_option_codes)} options for model {model_code} with trimline {trimline_code}"
            )
            return line_item
        except Exception as e:
            logger.error(
                f"[{self.market}] Error while loading trimline {trimline_code} from model link {model_link}, error: {e}"
            )
            return self._load_previous_day_line_item(model_link, trimline_code)

    def _load_previous_day_line_item(self, model_link, trimline_code):
        response = self.line_item_repository.load_model_filter_by_line_code(
            date=yesterday_dashed_str_with_key(),
            market=self.market,
            vendor=Vendor.AUDI,
            line_code=trimline_code,
        )
        if len(response) == 0:
            logger.info(
                f"[{self.market}] Unable to find previous line item for model {model_link} trimline: {trimline_code}"
            )
            return None
        if len(response) > 1:
            logger.error(
                f"[{self.market}] Expected length should be 1, but getting greater than 1 for model {model_link} trimline: {trimline_code}"
            )
            return None
        return response[0]

    def _get_trim_line_json(self, model_code, trimline_code, params):
        model_url = f"{DE_CONFIG_URL}&ids={params}&set={trimline_code}"
        logger.trace(
            f"[{self.market}] Scraping trimline {trimline_code} for model {model_code}"
        )
        trim_line_json = execute_request("get", model_url, self.session)
        if "conflicts" in trim_line_json:
            if trimline_code == "GBACFG1_2024":
                params = "GBACFG1_2024|B4B4|KU"
            elif trimline_code == "4KA0NY2_2024":
                params = "4KA0NY2_2024|A2A2|MZ|6FA"
            else:
                params = trim_line_json["conflicts"]["prstring"]
            trim_line_json = execute_request(
                "get", DE_CONFIG_URL, self.session, body={"ids": params}
            )
        return trim_line_json

    # Method to get included and extra options for a model.
    def get_line_option_codes(
        self,
        model_link: str,
        trimline_code: str,
        trimline_details: str,
        carinfo: dict,
    ) -> list[LineItemOptionCode]:
        line_option_codes = parse_line_item_options_for_trimline(
            trimline_details, carinfo["items"], self.market
        )
        try:
            options_type = self.get_options_types(carinfo)
            replace_options_type(line_option_codes, options_type)
        except Exception as e:
            logger.warning(
                f"[{self.market}] Unable to fetch generic option type for model {model_link} trimline {trimline_code}, {e}"
            )
        return line_option_codes

    def get_options_types(self, carinfo: str) -> dict:
        options_type_json = get_option_type_details(carinfo, self.session)
        # Check for data key in response json. So, the data is as expected.
        if "data" not in options_type_json:
            raise ValueError(f"{options_type_json}")
        options_type = parse_options_type(options_details_json=options_type_json)
        return options_type
