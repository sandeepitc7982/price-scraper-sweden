import json
import urllib
from asyncio import Future
from concurrent.futures import ThreadPoolExecutor
from typing import List

from loguru import logger
from requests import Session

from src.price_monitor.finance_scraper.audi.constants import (
    ANNUAL_MILEAGE,
    AUDI_UK_FINANCE_OPTION_ALL_MODEL_URL,
    AUDI_UK_FINANCE_OPTION_ALT_KEY_URL,
    AUDI_UK_FINANCE_OPTION_FOR_MODEL_URL,
    AUDI_UK_FINANCE_OPTION_MODEL_DETAILS_URL,
    CONTRACT_DURATION,
    CUSTOMER_DEPOSIT,
    OWN_CONTRIBUTION,
)
from src.price_monitor.finance_scraper.audi.finance_parser_uk import (
    parse_addon_options,
    parse_available_model_ranges_for_finance,
    parse_finance_line_item,
    parse_finance_option_details,
    parse_finance_options,
    parse_model_price,
    parse_pcp_finance_line_item,
    parse_pcp_finance_option_details,
)
from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.finance_item_repository import (
    FileSystemFinanceLineItemRepository,
)
from src.price_monitor.price_scraper.constants import E2E_TEST_LIST_SIZE
from src.price_monitor.utils.caller import execute_request
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


def find_available_finance_model_ranges(session: Session) -> list[dict]:
    all_models_url = AUDI_UK_FINANCE_OPTION_ALL_MODEL_URL
    all_models = execute_request("get", all_models_url, session)
    finance_able_models = parse_available_model_ranges_for_finance(all_models)
    return finance_able_models


class FinanceScraperAudiUk:
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
        self.vendor = Vendor.AUDI

    def scrape_finance_options_for_uk(self) -> list[FinanceLineItem]:
        response: list[FinanceLineItem] = []
        finance_able_model_ranges = find_available_finance_model_ranges(self.session)

        if self.config.get("e2e_tests"):
            finance_able_model_ranges = list(finance_able_model_ranges)[
                :E2E_TEST_LIST_SIZE
            ]
        jobs: List[Future] = []
        with ThreadPoolExecutor(
            thread_name_prefix="audi_uk_finance_scraper",
            max_workers=len(finance_able_model_ranges),
        ) as ex:
            for model_range in finance_able_model_ranges:
                logger.debug(
                    f"Fetching finance options for {model_range['model_range_code']}  {model_range['model_range_description']}"
                )
                scraped_line_jobs = ex.submit(
                    self._scrape_finance_option_for_model, model_range
                )
                jobs.append(scraped_line_jobs)
            for job in jobs:
                finance_line_item = job.result()
                if finance_line_item is not None:
                    response.extend(job.result())
        logger.info(f"[{self.market}] scraped {len(response)} Finance Items for Audi")
        return response

    def _scrape_finance_option_for_model(
        self, model_range: dict
    ) -> list[FinanceLineItem]:
        line_items = []
        try:
            line_items = self._scrape_finance_able_details_for_models(model_range)
            logger.info(
                f"Got {len(line_items)} for {model_range['model_range_code']}-{model_range['model_range_description']}"
            )
        except Exception as e:
            logger.error(
                f"[UK] Unable to scrape for model_link {model_range} , due to error: {e}. Loading From Previous Day....."
            )
            line_items = self.finance_line_item_repository.load_model_filter_by_model_range_description(
                date=yesterday_dashed_str_with_key(),
                market=self.market,
                vendor=Vendor.AUDI,
                model_range_description=model_range["model_range_description"],
            )
            logger.info(
                f"Loaded {len(line_items)} for {model_range['model_range_code']}-{model_range['model_range_description']}"
            )
        return line_items

    def _scrape_finance_able_details_for_models(self, model: dict) -> list:
        headers = {
            "apollographql-client-name": "fa-audi-finance",
            "apollographql-client-version": "6.0.1",
        }
        variables = {
            "carlineInput": {
                "brand": "A",
                "country": "gb",
                "language": "en",
                "carlineId": model["model_range_code"],
            },
            "featuresFilterInput": {
                "filterByFeatureState": "selected",
                "filterByFamilyIds": {
                    "familyIds": [
                        "color-type:metallic",
                        "color-type:pearl",
                        "color-type:uni",
                    ],
                    "mode": "INCLUSIVE",
                },
            },
        }
        extensions = {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "2b6fe2f74e7c6851ca13db4d3338c676c80827c2f7d25992452be8fec7b9f412",
            }
        }
        extensions_str = urllib.parse.quote(
            json.dumps(extensions, separators=(",", ":")), safe=""
        )
        variables_str = urllib.parse.quote(
            json.dumps(variables, separators=(",", ":")), safe=""
        )
        url = f"{AUDI_UK_FINANCE_OPTION_MODEL_DETAILS_URL}{variables_str}&extensions={extensions_str}"
        lines_json = execute_request("get", url, self.session, headers=headers)
        model_codes = []
        model_details = {}

        for trimlines in lines_json["data"]["configuredCarByCarline"][
            "carlineStructureCarline"
        ]["trimlines"]:
            for trimline in trimlines["models"]:
                model_code = trimline["defaultConfiguredCar"]["id"]["model"]["code"]
                version = trimline["defaultConfiguredCar"]["id"]["model"]["version"]
                extensions = trimline["defaultConfiguredCar"]["id"]["model"][
                    "extensionsPR7"
                ]
                model["model_description"] = trimline["engineName"]
                model["line_description"] = (
                    trimlines["id"].split("trimline_")[-1].upper()
                )
                model["line_code"] = trimlines["id"].split("trimline_")[-1]
                model["model_code"] = model_code
                joined_extension = "\\".join(extensions)
                if joined_extension:
                    model_code = f"{model_code}\\{version}\\{joined_extension}"
                else:
                    model_code = f"{model_code}\\{version}"
                model_codes.append(model_code)
                model["price"] = parse_model_price(trimline)
                model["year"] = trimline["defaultConfiguredCar"]["id"]["model"]["year"]
                model["default_configured_car_options"] = parse_addon_options(trimline)
                model_details[model_code] = model.copy()
        alt_keys = self._get_alt_keys_for_model(model_codes)

        finance_line_items = []

        for model_code, alt_key in alt_keys.items():
            finance_line_items.extend(
                self._get_available_finance_options(alt_key, model_details[model_code])
            )

        return finance_line_items

    def _get_alt_keys_for_model(self, model_codes: list) -> dict:
        alt_keys = {}
        headers = {
            "apollographql-client-name": "fa-audi-finance",
            "apollographql-client-version": "6.0.1",
        }
        url = AUDI_UK_FINANCE_OPTION_ALT_KEY_URL
        alt_key_details = execute_request(
            "post", url, self.session, headers=headers, body={"ModelCodes": model_codes}
        )
        for model in alt_key_details:
            alt_keys[model["ModelCode"]] = model["Capcode"]
        return alt_keys

    def _get_available_finance_options(self, alt_key: str, model: dict) -> list:
        url = AUDI_UK_FINANCE_OPTION_FOR_MODEL_URL

        payload = {
            "Request": {
                "@Domain": "AUDI.UK.CRS",
                "@Name": "Products",
                "Vehicle": {
                    "AltKey": alt_key,
                    "PriceTotal": model["price"],
                    "Year": model["year"],
                },
            }
        }
        headers = {
            "content-type": "application/json",
        }
        finance_options_json = execute_request(
            "post", url, self.session, body=payload, headers=headers
        )
        finance_options = parse_finance_options(finance_options_json)

        finance_line_items = []

        for finance_option in finance_options:
            finance_line_items.append(
                self._get_finance_details_for_finance_option(
                    finance_option, alt_key, model
                )
            )

        return finance_line_items

    def _get_finance_details_for_finance_option(
        self, finance_option: dict, alt_key: str, model: dict
    ) -> FinanceLineItem:
        url = AUDI_UK_FINANCE_OPTION_FOR_MODEL_URL
        payload = {
            "Request": {
                "@Domain": "AUDI.UK.CRS",
                "@Name": "Defaults",
                "Product": {"@ID": finance_option["finance_code"], "Parameter": []},
                "Vehicle": {
                    "AltKey": alt_key,
                    "PriceTotal": model["price"],
                    "Year": model["year"],
                },
            }
        }
        headers = {
            "content-type": "application/json",
        }

        return self._get_finance_line_item(finance_option, headers, model, payload, url)

    def _get_finance_line_item(
        self,
        finance_option: dict,
        headers: dict,
        model: dict,
        payload: dict,
        url: str,
    ) -> FinanceLineItem:
        is_pcp = "PCP" in finance_option["name"]

        parameters = [
            {"@ID": "Duration", "#text": CONTRACT_DURATION},
            {"@ID": "Mileage", "#text": ANNUAL_MILEAGE},
        ]
        if is_pcp:
            parameters.append({"@ID": "DownPayment", "#text": CUSTOMER_DEPOSIT})
        else:
            parameters.append({"@ID": "OwnContribution", "#text": OWN_CONTRIBUTION})
            parameters.append({"@ID": "FcmLevels", "#text": "None"})
        payload["Request"]["Product"]["Parameter"] = parameters

        finance_option_details_json = execute_request(
            "post", url, self.session, body=payload, headers=headers
        )

        if is_pcp:
            pcp_finance_option_details = parse_pcp_finance_option_details(
                finance_option_details_json
            )
            finance_line_item = parse_pcp_finance_line_item(
                pcp_finance_option_details, model
            )
        else:
            finance_option_details = parse_finance_option_details(
                finance_option_details_json
            )
            finance_line_item = parse_finance_line_item(
                finance_option, finance_option_details, model
            )

        return finance_line_item
