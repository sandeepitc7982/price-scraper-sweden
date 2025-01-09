from loguru import logger
from requests import Session

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.price_scraper.audi.constants import (
    AUDI_CAR_INFO_URL,
    AUDI_UK_BASE_URL,
    AUDI_UK_CONFIG_URL,
)
from src.price_monitor.price_scraper.audi.parser_helper import (
    parse_line_option_codes,
    parse_model_line_item,
)
from src.price_monitor.price_scraper.audi.parser_uk import (
    parse_available_model_range_links,
)
from src.price_monitor.price_scraper.constants import E2E_TEST_LIST_SIZE
from src.price_monitor.utils.caller import execute_request
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


class AudiScraperUK:
    def __init__(
        self,
        line_item_repository: FileSystemLineItemRepository,
        session: Session,
        config: dict,
    ):
        self.line_item_repository = line_item_repository
        self.session = session
        self.market = Market.UK
        self.config = config

    def scrape_models_for_uk(self):
        line_items = []

        model_range_url = AUDI_UK_BASE_URL + "/uk/web/en/models.html"
        homepage_text = execute_request(
            "get", model_range_url, self.session, response_format="text"
        )

        model_range_links = parse_available_model_range_links(homepage_text)

        if self.config.get("e2e_tests"):
            model_range_links = model_range_links[:E2E_TEST_LIST_SIZE]

        for model_range_link in model_range_links:
            try:
                line_item = self._scrape_models_from_model_range(model_range_link)
                line_items.extend(line_item)
                logger.info(
                    f"[UK] Scraped {len(line_item)} models for {model_range_link}"
                )
            except Exception as e:
                logger.error(
                    f"[UK] Unable to scrape for model_link {model_range_link} , due to error: {e}"
                )
                line_items.extend(
                    self._load_trim_lines_from_previous_day(model_range_link)
                )
        logger.info(f"[UK] Scraped {len(line_items)} for Audi")
        return line_items

    def _load_trim_lines_from_previous_day(self, model_range_link):
        series, model_range_code = model_range_link.split("/")[:2]
        response = self.line_item_repository.load_model_filter_by_model_range_code(
            date=yesterday_dashed_str_with_key(),
            market=self.market,
            vendor=Vendor.AUDI,
            series=series,
            model_range_code=model_range_code,
        )
        logger.info(
            f"[{self.market}] Loaded {len(response)} models for series {series} and model-range code {model_range_code}"
        )
        return response

    def _scrape_models_from_model_range(self, link):
        common_config_link = AUDI_CAR_INFO_URL + link + ".carinfo.mv-0-1216.10.json"
        models_link = AUDI_CAR_INFO_URL + link + ".modelsinfo.mv-0-1216.10.json"

        config_data = execute_request("get", common_config_link, self.session)

        logger.debug(
            f"[UK] Fetching available models for {config_data['configuration']['carlineName']}"
        )
        model_details = execute_request("get", models_link, self.session)["models"]
        return self._get_line_items_for_model(model_details, config_data, link)

    def _get_line_items_for_model(self, model_details, config_data, link):
        descriptions = config_data["items"]
        option_types = config_data["families"]
        url_params = config_data["configuration"]["items"]
        params_str = "|".join(url_params)
        line_items = []
        main_id = None
        for model_id, model_detail in model_details.items():
            try:
                if main_id is None:
                    main_id = f"{params_str}"
                line_item = self._request_line_item(
                    model_id, model_details, descriptions, option_types, link, main_id
                )

                if line_item:
                    line_items.append(line_item)
            except Exception as e:
                logger.error(
                    f"Unable to fetch details for model {model_id} and link: {link}, {e}"
                )
                line_item = self.line_item_repository.load_model_filter_by_model_code(
                    date=yesterday_dashed_str_with_key(),
                    market=self.market,
                    vendor=Vendor.AUDI,
                    model_code=model_id,
                )
                if len(line_item) > 1:
                    logger.error(
                        "[UK] Detected more than one model for same unique code."
                    )

                line_items.extend(line_item)
        return line_items

    def _request_line_item(
        self,
        model_id: str,
        model_details,
        descriptions,
        option_types,
        link,
        main_id,
    ):
        # Setting up a parameter 'main_id' for api calls of trimlines details.
        # It is set up only once for each model and used by all trimlines calls of that model.
        params = {"ids": main_id, "set": model_id}
        models_data = execute_request(
            "get", AUDI_UK_CONFIG_URL, self.session, body=params
        )

        if "configuration" not in models_data and "conflicts" not in models_data:
            logger.info(
                f"[UK] Unable to parse Launch Edition line, response: {models_data}, model details: {model_details}"
            )
            return

        # For specific Launch Edition line_item, APIs fails, in that we case need to add
        # conflicting option params to the API.
        if "prices" in models_data["configuration"]:
            line_item = parse_model_line_item(
                models_data, link, self.market, model_details
            )
        elif "choiceIds" in models_data["conflicts"]:
            params = {
                "ids": f"{models_data['conflicts']['prstring']}",
            }
            models_data = execute_request(
                "get", AUDI_UK_CONFIG_URL, self.session, body=params
            )
            if "error" in models_data["header"]:
                params["action"] = "accept"
                models_data = execute_request(
                    "get", AUDI_UK_CONFIG_URL, self.session, body=params
                )
            line_item = parse_model_line_item(
                models_data, link, self.market, model_details
            )
        else:
            logger.error(
                f"[UK] Unable to parse Launch Edition line for response: {models_data}, model details: {model_details}"
            )
            return
        line_item.line_option_codes = parse_line_option_codes(
            models_data, descriptions, option_types, Market.UK
        )
        return line_item
