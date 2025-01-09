from typing import List

from loguru import logger

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.vendor import Vendor
from src.price_monitor.price_scraper.mercedes_benz.constants import (
    HASH_VALUE_FOR_MODEL_SERIES_URL,
    MARKET_MAP_MODEL_SERIES_URL,
    MODEL_SERIES_URL,
)
from src.price_monitor.price_scraper.mercedes_benz.parser import (
    parse_line_item,
    parse_line_options,
    parse_trim_line,
    parse_trim_line_codes,
)
from src.price_monitor.utils.caller import execute_request
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


class ModelScraper:
    def __init__(
        self,
        market,
        session,
        line_item_repository,
        config={"feature_toggle": {"is_type_hierarchy_enabled_MB": True}},
    ):
        self.config = config
        self.isTypeHierarchyEnabled = config["feature_toggle"][
            "is_type_hierarchy_enabled_MB"
        ]
        self.session = session
        self.market = market
        self.line_item_repository = line_item_repository

    def get_model(self, data: dict, version: str):
        vehicles = data["vehicles"]
        class_body_names = data["classBodyNames"][0]
        model_options: dict
        basic_line_item: LineItem
        response: List[LineItem] = []
        for vehicle in vehicles:
            vehicle_id = vehicle["vehicleId"]
            engine_performance = vehicle["tags"][0]["value"]
            try:
                trim_line_codes = self._get_trim_line_codes(vehicle_id, version)
                model_options = self._scrape_options(vehicle_id, version)
            except Exception as e:
                model_code = vehicle["baumuster"]
                model_description = vehicle["name"]
                logger.error(
                    f"[{self.market}] Failed to scrape trim lines for model: {model_description} for {Vendor.MERCEDES_BENZ}."
                    f"Reason: '{e}'. Loading options from previous dataset..."
                )
                line_item_list = (
                    self.line_item_repository.load_model_filter_by_model_code(
                        date=yesterday_dashed_str_with_key(),
                        market=self.market,
                        vendor=Vendor.MERCEDES_BENZ,
                        model_code=model_code,
                    )
                )
                if len(line_item_list) > 0:
                    response.extend(line_item_list)
                    logger.info(
                        f"[{self.market}] Loaded {len(line_item_list)} trim lines for model: {model_description} for {Vendor.MERCEDES_BENZ}."
                    )
                continue
            basic_line_item = self._get_basic_line(
                class_body_names, model_options, vehicle, engine_performance
            )
            if len(trim_line_codes) != 0:
                response.extend(
                    self._append_trim_lines(
                        basic_line_item,
                        model_options,
                        trim_line_codes,
                        vehicle_id,
                        version,
                        engine_performance,
                    )
                )
            else:
                response.append(basic_line_item)
        return response

    def _get_trim_line_codes(self, vehicle_id, version):
        model_options = self._scrape_options(vehicle_id, version)
        trim_line_codes = parse_trim_line_codes(model_options)
        return trim_line_codes

    def _get_basic_line(
        self, class_body_names, model_options, vehicle, engine_performance
    ):
        basic_line: str = "BASIC LINE"
        basic_line_item = parse_line_item(
            vehicle, class_body_names, self.market, engine_performance
        )
        basic_line_item.line_description = basic_line
        try:
            basic_line_item.line_option_codes = parse_line_options(
                self.isTypeHierarchyEnabled, model_options, True, basic_line
            )
        except Exception as e:
            logger.error(
                f"[{self.market}] Failed to scrape options for {Vendor.MERCEDES_BENZ}, for model:  {basic_line_item.model_description} "
                f"{basic_line_item.line_description} Reason: '{e}'. Loading options from previous dataset..."
            )
            basic_line_item.line_option_codes = (
                self.line_item_repository.load_line_option_codes_for_line_code(
                    date=yesterday_dashed_str_with_key(),
                    market=self.market,
                    vendor=Vendor.MERCEDES_BENZ,
                    series=basic_line_item.series,
                    model_code=basic_line_item.model_code,
                    line_code=basic_line_item.line_code,
                )
            )
            logger.info(
                f"[{self.market}] Loaded {len(basic_line_item.line_option_codes)} options for {Vendor.MERCEDES_BENZ}, for model:  "
                f"{basic_line_item.model_description} {basic_line_item.line_description}."
            )
        return basic_line_item

    def _scrape_options(self, vehicle_id: str, version: str) -> dict:
        # replacing the hashtag by the hash_value in the vehicle_id to build the url.
        vehicle_id = vehicle_id.replace("#", HASH_VALUE_FOR_MODEL_SERIES_URL)
        url = (
            f"{MODEL_SERIES_URL}{MARKET_MAP_MODEL_SERIES_URL.get(self.market)}/CCci/{version}/vehicles/{vehicle_id}"
            f"/selectables"
        )
        model_page_json = execute_request("get", url, self.session)
        return model_page_json

    def _append_trim_lines(
        self,
        basic_line_item: LineItem,
        model_options: dict,
        trim_line_codes: List,
        vehicle_id: str,
        version: str,
        engine_performance: str,
    ) -> List[LineItem]:
        trim_line_description: str
        line_item: LineItem
        response: List[LineItem] = []
        flag: bool = False
        for trim_line_code in trim_line_codes:
            trim_line_description = model_options["components"][trim_line_code]["name"]
            if trim_line_description != "V8-Styling-Paket Exterieur":
                if model_options["components"][trim_line_code]["selected"]:
                    flag = True
                try:
                    line_item = self._scrape_trim_line(
                        vehicle_id,
                        trim_line_code,
                        trim_line_description,
                        version,
                        engine_performance,
                    )
                    response.append(line_item)
                except Exception as e:
                    logger.error(
                        f"[{self.market}] Failed to scrape {trim_line_description} trim line for {Vendor.MERCEDES_BENZ}, for model: "
                        f"{basic_line_item.model_description}. Reason: '{e}'. Loading options from previous dataset..."
                    )
                    line_items = (
                        self.line_item_repository.load_model_filter_by_line_code(
                            date=yesterday_dashed_str_with_key(),
                            market=self.market,
                            vendor=Vendor.MERCEDES_BENZ,
                            line_code=basic_line_item.model_code + "/" + trim_line_code,
                        )
                    )
                    if len(line_items) > 0:
                        line_item = line_items[0]
                        logger.info(
                            f"[{self.market}] Loaded {line_item.line_description} trim line for "
                            f"{basic_line_item.model_description}"
                        )
                        response.append(line_item)
                    else:
                        logger.info(
                            f"[{self.market}] Could not Load trim line for {basic_line_item.model_description}"
                        )
        if not flag:
            response.append(basic_line_item)
        return response

    def _get_trim_line(
        self,
        data: dict,
        trim_line_code: str,
        trim_line_description: str,
        version: str,
        engine_performance: str,
    ) -> LineItem:
        line_item: LineItem = parse_trim_line(
            self.market,
            data,
            trim_line_code,
            trim_line_description,
            engine_performance,
        )
        try:
            line_option = self._scrape_options(data["vehicle"]["vehicleId"], version)
            line_item.line_option_codes = parse_line_options(
                self.isTypeHierarchyEnabled,
                line_option,
                False,
                line_item.line_description,
            )
        except Exception as e:
            logger.error(
                f"[{self.market}] Failed to scrape options for {Vendor.MERCEDES_BENZ}, for model:  {line_item.model_description} "
                f"{line_item.line_description} Reason: '{e}'. Loading options from previous dataset..."
            )
            line_item.line_option_codes = (
                self.line_item_repository.load_line_option_codes_for_line_code(
                    date=yesterday_dashed_str_with_key(),
                    market=self.market,
                    vendor=Vendor.MERCEDES_BENZ,
                    series=line_item.series,
                    model_code=line_item.model_code,
                    line_code=line_item.line_code,
                )
            )
            logger.info(
                f"[{self.market}] Loaded {len(line_item.line_option_codes)} options for {Vendor.MERCEDES_BENZ}, for model:  "
                f"{line_item.model_description} {line_item.line_description}."
            )
        return line_item

    def _scrape_trim_line(
        self,
        vehicle_id: str,
        trim_line_code: str,
        trim_line_description: str,
        version: str,
        engine_performance: str,
    ) -> LineItem:
        vehicle_id = vehicle_id.replace("#", HASH_VALUE_FOR_MODEL_SERIES_URL)
        url = (
            f"{MODEL_SERIES_URL}{MARKET_MAP_MODEL_SERIES_URL.get(self.market)}/CCci/{version}/vehicles/{vehicle_id}"
            f"/add/{trim_line_code}"
        )
        model_page_json = execute_request("get", url, self.session)
        return self._get_trim_line(
            model_page_json,
            trim_line_code,
            trim_line_description,
            version,
            engine_performance,
        )
