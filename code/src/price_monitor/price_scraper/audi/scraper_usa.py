from loguru import logger
from requests import Session

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.price_scraper.audi.constants import (
    AUDI_USA_BASE_URL,
    AUDI_USA_CONFIG_URL,
)
from src.price_monitor.price_scraper.audi.parser_helper import (
    parse_line_option_codes,
    parse_model_line_item,
)
from src.price_monitor.price_scraper.audi.parser_usa import (
    parse_available_model_range_links,
)
from src.price_monitor.price_scraper.constants import E2E_TEST_LIST_SIZE
from src.price_monitor.utils.caller import execute_request
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


class AudiScraperUSA:
    def __init__(
        self,
        line_item_repository: FileSystemLineItemRepository,
        session: Session,
        config: dict,
    ):
        self.line_item_repository = line_item_repository
        self.session = session
        self.market = Market.US
        self.config = config

    def scrape_models_for_usa(self):
        line_items = []

        model_range_url = AUDI_USA_BASE_URL + "/us/web/en/models.html"
        homepage_text = execute_request(
            "get", model_range_url, self.session, response_format="text"
        )

        links_having_price, links_not_having_price = parse_available_model_range_links(
            homepage_text
        )

        if self.config.get("e2e_tests"):
            links_having_price = links_having_price[:E2E_TEST_LIST_SIZE]

        for model_range_link in links_having_price:
            try:
                line_items.extend(
                    self._scrape_models_from_model_range(model_range_link)
                )
            except Exception as e:
                logger.error(
                    f"[US] Unable to scrape for model_link {model_range_link} , due to error: {e}"
                )
                line_items.extend(
                    self._load_trim_lines_from_previous_day(model_range_link)
                )
        for model_range_link in links_not_having_price:
            logger.info(
                f"[{self.market}] model {model_range_link} doesn't have price. Loading previous day price."
            )
            line_items.extend(self._load_trim_lines_from_previous_day(model_range_link))
        return line_items

    def _load_trim_lines_from_previous_day(self, model_range_link):
        series, model_range_code = model_range_link.split("/")[5:7]
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
        common_config_link = AUDI_USA_BASE_URL + link + ".carinfo.mv-0-1216.10.json"
        models_link = AUDI_USA_BASE_URL + link + ".modelsinfo.mv-0-1216.10.json"

        config_data = execute_request("get", common_config_link, self.session)

        logger.debug(
            f"[US] Fetching available models for {config_data['configuration']['carlineName']}"
        )
        model_details = execute_request("get", models_link, self.session)["models"]

        return self._get_line_items_for_model(model_details, config_data, link)

    def _get_line_items_for_model(self, model_details, config_data, link):
        descriptions = config_data["items"]
        url_params = config_data["configuration"]["items"][1:]
        params_str = "|".join(url_params)
        line_items = []
        main_id = None
        for model_id, model_detail in model_details.items():
            try:
                if main_id is None:
                    main_id = f"{model_id}|{params_str}"
                line_item = self._request_line_item(
                    model_id, model_details, descriptions, link, main_id
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
                        "[US] Detected more than one model for same unique code."
                    )

                line_items.extend(line_item)
        return line_items

    def _request_line_item(
        self,
        model_id: str,
        model_details,
        descriptions,
        link,
        main_id,
    ):
        # Seting up a parameter 'main_id' for api calls of trimlines details. It is setup only once for each model and used by all trimlines calls of that model.

        params = {"ids": main_id, "set": model_id}
        models_data = execute_request(
            "get", AUDI_USA_CONFIG_URL, self.session, body=params
        )

        if "configuration" not in models_data and "conflicts" not in models_data:
            logger.info(
                f"[US] Unable to parse Launch Edition line, response: {models_data}, model details: {model_details}"
            )
            return

        # For specific Launch Edition lineitem, APIs fails, in that we case need to add conflicting option params to the API.
        if "prices" in models_data["configuration"]:
            line_item = parse_model_line_item(models_data, link, self.market, "")
        elif "choiceIds" in models_data["conflicts"]:
            params = {
                "ids": f"{models_data['conflicts']['prstring']}",
            }
            models_data = execute_request(
                "get", AUDI_USA_CONFIG_URL, self.session, body=params
            )
            if "error" in models_data["header"]:
                params["action"] = "accept"
                models_data = execute_request(
                    "get", AUDI_USA_CONFIG_URL, self.session, body=params
                )
            line_item = parse_model_line_item(models_data, link, self.market, "")
        else:
            logger.error(
                f"[US] Unable to parse Launch Edition line for response: {models_data}, model details: {model_details}"
            )
            return
        line_item.line_option_codes = parse_line_option_codes(
            models_data, descriptions, Market.US
        )
        return line_item
