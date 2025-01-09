import json
from typing import List

import requests
from loguru import logger
from retry import retry

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.bmw.constants import (
    API_KEY_URL,
    BASE_URL,
    CONFIGURATION_STATE_PATH,
    CONSTRUCTIBILITY_PATH,
    LOCALISATION_PATH,
    MARKET_MAP,
    MODEL_MATRICES_PATH,
    PUBLIC_PRICING_PATH,
    X_API_KEY,
)
from src.price_monitor.price_scraper.bmw.parser import (
    STANDARD_LINES,
    _get_available_language,
    adjust_line_options,
    parse_api_token,
    parse_configuration_state,
    parse_constructible_extra_options_for_line,
    parse_effect_date,
    parse_extra_available_options,
    parse_is_volt_48,
    parse_ix_model_codes,
    parse_lines_string,
    parse_model_matrix_to_line_items,
    parse_options_price,
    parse_packages_price,
    parse_tax_date,
)
from src.price_monitor.price_scraper.bmw.scraper_usa import scrape_models_for_usa
from src.price_monitor.price_scraper.constants import NOT_AVAILABLE, E2E_TEST_LIST_SIZE
from src.price_monitor.price_scraper.vendor_scraper import VendorScraper
from src.price_monitor.utils.caller import execute_request
from src.price_monitor.utils.clock import (
    today_dashed_str,
    yesterday_dashed_str_with_key,
)


def get_updated_token():
    api_token: str
    try:
        token_content = execute_request("get", API_KEY_URL, response_format="text")
        api_token = parse_api_token(token_content)
    except Exception as e:
        api_token = NOT_AVAILABLE
        logger.error(
            f"Failed to get updated token. Reason: {e}. Setting BMW token to N/A "
        )
    return api_token


def get_model_matrix(market, session, headers, req=None) -> dict:
    """Wrapper function to generate a request.
    Creates a get-request for the website as input, returns the information about all lines.
    """
    if req is None:
        req = (
            f"{BASE_URL}{MODEL_MATRICES_PATH}/{MARKET_MAP[market]}/effect-dates/{today_dashed_str()}"
            f"/order-dates/{today_dashed_str()}?closest-fallback=true"
        )
    logger.trace(f"[{market}] Fetching available models at: {req}")
    return execute_request("get", url=req, session=session, headers=headers)


def get_ix_models(market, req_header, session=requests.Session()):
    url = f"{BASE_URL}{MODEL_MATRICES_PATH}/{MARKET_MAP[market]}/effect-dates/{today_dashed_str()}/order-dates/{today_dashed_str()}?closest-fallback=true"
    url = url.replace("bmwCar", "bmwi")
    model_matrix_for_i = get_model_matrix(market, session, req_header, url)
    bmw_i_line_items = parse_model_matrix_to_line_items(model_matrix_for_i, market)
    return model_matrix_for_i, bmw_i_line_items


def get_configuration_state_and_is_volt_48(
    model_code: str,
    effect_date: str,
    included_options_str: str,
    ix_models: str,
    headers,
    session,
    market: Market,
):
    url = f"{BASE_URL}{CONFIGURATION_STATE_PATH}/{MARKET_MAP[market]}/effect-dates/{effect_date}/order-dates/{today_dashed_str()}/models/{model_code}?included-elements={included_options_str}&mandatory-elements=&add-rules-for-mandatory-element-classes=fabric,paint,rim&debug=false"
    if model_code in ix_models:
        url = url.replace("bmwCar", "bmwi")
    state_and_is_volt_48_json = execute_request("get", url, session, headers=headers)
    if "classifiedConfiguration" not in state_and_is_volt_48_json:
        raise ValueError(
            f"[{market}] Failed to find configuration state and is_volt_48 flag for model {model_code}, "
            f"{state_and_is_volt_48_json}"
        )
    return state_and_is_volt_48_json


class BMWScraper(VendorScraper):
    """This class initialises the scraper functionality for the BMW car prices.
    The best way to initialise this class is with a configuration dict or .ini file."""

    def __init__(self, line_item_repository, config: dict = None) -> None:
        self.req_header = {
            "Content-Type": "application/json",
        }
        self.markets: list[Market] = []
        self.line_item_repository = line_item_repository
        self.language_support = {}
        self.config = config
        self.markets = config["scraper"]["enabled"][Vendor.BMW]

    def scrape_models(self, market: Market) -> List[LineItem]:
        response: List[LineItem] = []

        # For BMW APIs we need an API Key, which is common for all markets.
        self.req_header[X_API_KEY] = get_updated_token()

        try:
            models = self._scrape_models_for_market(market=market)
            if len(models) == 0:
                raise ValueError("Something went wrong, Fetched 0 models")
            response.extend(models)
            logger.info(f"Scraped {len(response)} models for market {market}")
        except Exception as e:
            logger.exception(
                f"[{market}] Failed to scrape models for {Vendor.BMW}, {e}. Loading previous dataset..."
            )
            response.extend(
                self.line_item_repository.load_market(
                    date=yesterday_dashed_str_with_key(),
                    market=market,
                    vendor=Vendor.BMW,
                )
            )
        return response

    @retry(tries=3, delay=1, backoff=2)
    def _scrape_models_for_market(self, market: Market) -> List[LineItem]:
        response: List[LineItem] = []

        logger.info(f"Scraping car lines for market {market}")

        # This method is not thread safe since the market and session variables are shared.
        self.market = market
        self.session = requests.Session()
        self.IX_MODELS = []

        if market == Market.US:
            return scrape_models_for_usa(
                line_item_repository=self.line_item_repository, config=self.config
            )
        model_matrix = get_model_matrix(self.market, self.session, self.req_header)
        parsed_line_items = parse_model_matrix_to_line_items(model_matrix, self.market)

        # For few APIs we need to provide the language of corresponding market in the URL.
        self.language_support[self.market] = _get_available_language(
            list(model_matrix.values())[0], market
        )

        logger.debug(
            f"[{self.market}] Found {len(parsed_line_items)} potential line items"
        )

        if self.config.get("e2e_tests"):
            parsed_line_items = parsed_line_items[:E2E_TEST_LIST_SIZE]

        response.extend(
            self.append_available_options(market, model_matrix, parsed_line_items)
        )

        # Scraping IX models specifically for BMW UK
        if market == Market.UK:
            bmw_i_model_matrix, bmw_i_line_items = get_ix_models(
                market, self.req_header, self.session
            )
            self.IX_MODELS = parse_ix_model_codes(bmw_i_model_matrix)
            response.extend(
                self.append_available_options(
                    market, bmw_i_model_matrix, bmw_i_line_items
                )
            )

        logger.info(f"[{self.market}] Found {len(parsed_line_items)} line items")
        return response

    def append_available_options(self, market, model_matrix, parsed_line_items):
        response = []
        for line_item in parsed_line_items:
            try:
                response.append(
                    self._add_available_options_for_line(
                        market, line_item, model_matrix
                    )
                )
            except Exception as e:
                logger.error(
                    f"[{market}] Failed to scrape options for {Vendor.BMW}, for model:  {line_item.series} "
                    f"{line_item.model_range_description} {line_item.model_description} {line_item.line_description}. "
                    f"Reason: '{e}'. Loading options from previous dataset..."
                )
                line_item.line_option_codes = (
                    self.line_item_repository.load_line_option_codes_for_line_code(
                        date=yesterday_dashed_str_with_key(),
                        market=self.market,
                        vendor=Vendor.BMW,
                        series=line_item.series,
                        model_code=line_item.model_code,
                        line_code=line_item.line_code,
                    )
                )
                logger.info(
                    f"[{self.market}] Loaded {len(line_item.line_option_codes)} Options for model: "
                    f"{line_item.series} {line_item.model_range_description} {line_item.model_description} "
                    f"{line_item.line_description}"
                )
                response.append(line_item)
        return response

    def _add_available_options_for_line(
        self, market, line_item, model_matrix
    ) -> LineItem:
        logger.debug(
            f"[{self.market}] Fetching available options for [{line_item.model_code}] {line_item.model_description} "
            f"with line {line_item.line_code} {line_item.line_description}"
        )
        lines_str = parse_lines_string(model_matrix, line_item)

        # Extracting the effect date and tax date from the model_matrix.
        # They are required as param for several API calls.
        effect_date = parse_effect_date(
            model_matrix=model_matrix,
            series=line_item.series,
            model_range_code=line_item.model_range_code,
            model_code=line_item.model_code,
        )
        tax_date = parse_tax_date(
            model_matrix=model_matrix,
            series=line_item.series,
            model_range_code=line_item.model_range_code,
            model_code=line_item.model_code,
        )

        # Till now, we have default/included options, now we are fetching the extra options for the same.
        available_options = self.get_available_options_for_model(
            model_code=line_item.model_code,
            effect_date=effect_date,
            tax_date=tax_date,
        )
        logger.trace(
            f"[{self.market}] Found {len(available_options)} available options for model {line_item.model_description}"
        )

        # List of default/included options, it will be needed when we fetch extra options and their prices.
        included_options = list(line_item.line_option_code_keys())
        included_options.sort()

        state_and_is_volt_48_content = get_configuration_state_and_is_volt_48(
            model_code=line_item.model_code,
            effect_date=effect_date,
            included_options_str=",".join(included_options),
            ix_models=self.IX_MODELS,
            headers=self.req_header,
            session=self.session,
            market=self.market,
        )

        # Fetching configuration state, required to check the constructability of the options.
        configuration_state = parse_configuration_state(state_and_is_volt_48_content)

        # is_volt_48 flag required for pricing APIs.
        is_volt_48_variant = parse_is_volt_48(state_and_is_volt_48_content)

        line_item.line_option_codes = self.add_available_options(
            line_item, configuration_state, available_options, lines_str
        )

        # Getting the prices of available options.
        options_price = self.get_options_price(
            line_item.model_code,
            included_options,
            list(available_options.keys()),
            tax_date,
            effect_date,
            is_volt_48_variant,
        )

        # Filling in the option properties. Ex. Description, Price, etc.
        line_item.line_option_codes = adjust_line_options(
            market,
            line_item.line_option_codes,
            available_options,
            options_price,
            line_item.line_description,
        )
        return line_item

    def get_available_options_for_model(
        self,
        model_code: str,
        effect_date: str,
        tax_date: str,
    ) -> dict:
        """Given a model 'model code', it calls the BMW-API to retrieve all available options for that model"""
        req = self._generate_get_request(
            req_type="localisation_vehicle_check",
            model_code=model_code if len(model_code) > 0 else None,
            effect_date=effect_date,
            tax_date=tax_date,
        )

        available_options_json = execute_request(
            "get", req, self.session, headers=self.req_header
        )
        if type(available_options_json) is not dict or len(available_options_json) == 0:
            raise ValueError(
                f"{self.market}] Failed to find available options for model {model_code}, {available_options_json}"
            )
        return available_options_json

    # Helper functions from here on out.
    def _generate_get_request(
        self,
        req_type,
        model_code: str,
        line_code: str = None,
        options_str: str = None,
        configuration_state: str = None,
        effect_date: str = None,
        tax_date: str = None,
        is_volt_48_variant: bool = None,
        lines_str: str = None,
    ) -> str:
        """Given the parameters, generate an appropriate get-request, returns string"""

        if req_type == "localisation_vehicle_check":
            url = (
                f"{BASE_URL}{LOCALISATION_PATH}/{MARKET_MAP[self.market]}/effect-dates/{effect_date}/"
                f"order-dates/{tax_date}/applications/connext/models/"
                f"{model_code}/options/languages/{self.language_support[self.market]}?closest-fallback=true"
            )

        elif req_type == "constructibility_check":
            if line_code in STANDARD_LINES:
                url = f"{BASE_URL}{CONSTRUCTIBILITY_PATH}/{configuration_state}/add-element-bulk-invocation/{options_str}?excluded-elements={lines_str}&mandatory-elements="
            else:
                url = f"{BASE_URL}{CONSTRUCTIBILITY_PATH}/{configuration_state}/add-element-bulk-invocation/{options_str}?excluded-elements=&mandatory-elements={line_code}"

        elif req_type == "package_pricing":
            url = f"{BASE_URL}{PUBLIC_PRICING_PATH}/{MARKET_MAP[self.market]}/models/{model_code}/tax-dates/{tax_date}/package-pricing?effect-date={effect_date}&order-date={today_dashed_str()}&option-codes={options_str}&ignore-invalid-option-codes=true&ignore-options-with-undefined-prices=true&params.isVolt48Variant={json.dumps(is_volt_48_variant)}&rounding-scale=1"

        if model_code in self.IX_MODELS:
            url = url.replace("bmwCar", "bmwi")
        return url

    def get_options_price(
        self,
        model_code: str,
        options: list,
        available_options: list,
        tax_date: str,
        effect_date: str,
        is_volt_48_variant: bool,
    ) -> dict:
        """Wrapper function to execute a request
        Gets a post request for a option's price."""
        req, body = self.generate_pricing_request_body(
            model_code=model_code,
            options=options,
            available_options=available_options,
            tax_date=tax_date,
            effect_date=effect_date,
            is_volt_48_variant=is_volt_48_variant,
        )
        options_price_json = execute_request(
            "post", req, self.session, headers=self.req_header, body=body
        )

        if "availableOptions" not in options_price_json:
            raise ValueError(
                f"[{self.market}] Failed to find options price for model {model_code}, {options_price_json}"
            )

        options_price = parse_options_price(options_price_json)

        # In options_price we were getting wrong prices for packages.
        # So, we are explicitly fetching price of packages from different API And updating them with package prices in options_prices we have previously.
        package_price_details = self.get_packages_price(
            model_code,
            effect_date,
            tax_date,
            ",".join(options),
            is_volt_48_variant,
        )

        packages_price = parse_packages_price(package_price_details)
        options_price.update(packages_price)
        return options_price

    def generate_pricing_request_body(
        self,
        model_code: str,
        options: list,
        available_options: list,
        tax_date: str,
        effect_date: str,
        is_volt_48_variant: bool,
    ) -> tuple:
        """Given the parameters, generate an appropriate post-request, returns tuple of request and body."""
        body = {
            "configuration": {
                "model": model_code,
                "selectedOptions": options,
                "availableOptions": available_options,
            },
            "validityDates": {
                "taxDate": tax_date,
                "effectDate": effect_date,
            },
            "settings": {
                "priceTree": "DEFAULT",
                "ignoreOptionsWithUndefinedPrices": True,
                "ignoreInvalidOptionCodes": True,
                "accessoriesMustFitConfiguration": False,
                "roundingScale": 1,
            },
            "additionalParams": {
                "isVolt48Variant": {
                    "key": "isVolt48Variant",
                    "value": is_volt_48_variant,
                }
            },
        }
        logger.trace(
            f"Generating option prices request for model {model_code} with body: {body}"
        )
        url = f"{BASE_URL}{PUBLIC_PRICING_PATH}/{MARKET_MAP[self.market]}"
        if model_code in self.IX_MODELS:
            url = url.replace("bmwCar", "bmwi")

        return url, body

    # Function to get union of available options and included/default options for a line item without price.
    def add_available_options(
        self,
        line_item: LineItem,
        configuration_state: str,
        model_available_options: dict,
        lines_str: str,
    ) -> list[LineItemOptionCode]:
        line_option_codes = line_item.line_option_codes.copy()
        included_options = line_item.line_option_code_keys()

        # Note : When we fetch available options, it will give all the available options for a model
        # irrespective of trimline. So, in this method we are also filtering it out for specific trim-line.

        # Filtering all available options on some pre-conditions.
        possible_extra_options_str = parse_extra_available_options(
            model_available_options, included_options, lines_str
        )

        # Checking the constructability of all possible options for a trim line.
        constructability_status = self.get_constructibility_check(
            line_item.model_code,
            line_item.line_code,
            possible_extra_options_str,
            configuration_state,
            lines_str,
        )
        line_option_codes.extend(
            parse_constructible_extra_options_for_line(constructability_status)
        )

        return line_option_codes

    def get_constructibility_check(
        self,
        model_code: str,
        line_code: str,
        options_str: str,
        configuration_state: str,
        lines_str: str,
    ) -> dict:
        req = self._generate_get_request(
            req_type="constructibility_check",
            model_code=model_code,
            line_code=line_code,
            options_str=options_str,
            configuration_state=configuration_state,
            lines_str=lines_str,
        )

        constructability_json = execute_request(
            "get", req, self.session, headers=self.req_header
        )
        if type(constructability_json) is not dict:
            raise ValueError(
                f"[{self.market}] Failed to check constructability of available options for model {model_code} "
                f"and line {line_code}, {constructability_json}"
            )
        return constructability_json

    def get_packages_price(
        self,
        model_code: str,
        effect_date: str,
        tax_date: str,
        options_str: str,
        is_volt_48_variant: bool,
    ) -> dict:
        req = self._generate_get_request(
            req_type="package_pricing",
            model_code=model_code,
            effect_date=effect_date,
            tax_date=tax_date,
            options_str=options_str,
            is_volt_48_variant=is_volt_48_variant,
        )

        packages_price_json = execute_request(
            "get", req, self.session, headers=self.req_header
        )

        if "packagePricingList" not in packages_price_json:
            raise ValueError(
                f"[{self.market}] Failed to find price of packages having model {model_code}, {packages_price_json}"
            )
        return packages_price_json
