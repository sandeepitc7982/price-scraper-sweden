import collections

from loguru import logger

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.utils.clock import today_dashed_str_with_key


class DataQualityCheck:
    def __init__(self, line_item_repository: FileSystemLineItemRepository):
        self.line_item_repository = line_item_repository
        self.NEW_LINE_CHARACTER = "\n"
        self.market = ""
        self.vendor = ""

    def run_quality_checks_all_vendors(self, config):
        vendor_markets_dict = config["scraper"]["enabled"]

        for vendor, markets in vendor_markets_dict.items():
            self.run_check_for_vendor_and_market(vendor=vendor, markets=markets)

    def run_check_for_vendor_and_market(self, vendor: Vendor, markets: list[Market]):
        for market in markets:
            logger.info(f"Running data quality checks for {vendor}-{market}")
            line_item_list = self.line_item_repository.load_market(
                date=today_dashed_str_with_key(),
                market=market,
                vendor=vendor,
            )
            self.market = market
            self.vendor = vendor
            self.assert_output(line_items=line_item_list, market=market)

    def assert_output(self, line_items: list[LineItem], market: Market):
        line_items_in_market = list(
            filter(lambda item: (item.market == market), line_items)
        )
        if len(line_items_in_market) == 0:
            logger.warning(f"[{self.market}-{self.vendor}] Zero Models Found")
        else:
            self._check_for_model_duplication(line_items)
            for line_item in line_items_in_market:
                self._check_for_negative_price_for_model(line_item)
                if not (self.vendor == Vendor.BMW and self.market == Market.US):
                    self._check_for_negative_price_for_options(line_item)
                self._check_for_new_line_character_in_descriptions(line_item)
                self._check_for_included_and_excluded_option_count(line_item)
                if self.vendor != Vendor.BMW:
                    self._check_for_included_options_with_non_zero_price(line_item)

    def _check_for_included_and_excluded_option_count(self, line_item):
        number_options_included = 0
        number_options_excluded = 0
        for option in line_item.line_option_codes:
            if not isinstance(option.included, bool):
                logger.warning(
                    f"[{self.market}-{self.vendor}] Expected to be Boolean but Found {type(option.included)}"
                )
            if bool(option.included):
                number_options_included += 1
            else:
                number_options_excluded += 1
        if number_options_included == 0:
            logger.warning(
                f"[{self.market}-{self.vendor}] Zero count of options included for options in model_range:{line_item.model_range_description} model_description:{line_item.model_description} line_description:{line_item.line_description}"
            )
        if number_options_excluded == 0:
            logger.warning(
                f"[{self.market}-{self.vendor}] Zero count of options excluded for options in model_range:{line_item.model_range_description} model_description:{line_item.model_description} line_description:{line_item.line_description}"
            )

    def _check_for_new_line_character_in_descriptions(self, line_item):
        if self._check_for_new_line_character(line_item.model_range_description):
            logger.warning(
                f"[{self.market}-{self.vendor}] New Line Character Error in Model_Range_Description for model_range:{line_item.model_range_description} model_description:{line_item.model_description} line_description:{line_item.line_description}"
            )
        if self._check_for_new_line_character(line_item.model_description):
            logger.warning(
                f"[{self.market}-{self.vendor}] New Line Character Error in Model_Description for model_range:{line_item.model_range_description} model_description:{line_item.model_description} line_description:{line_item.line_description}"
            )
        if self._check_for_new_line_character(line_item.line_description):
            logger.warning(
                f"[{self.market}-{self.vendor}] New Line Character Error in Line_Description for model_range:{line_item.model_range_description} model_description:{line_item.model_description} line_description:{line_item.line_description}"
            )
        for option in line_item.line_option_codes:
            if self._check_for_new_line_character(option.description):
                logger.warning(
                    f"[{self.market}-{self.vendor}] New Line Character Error in Option_Description for model_range:{line_item.model_range_description} model_description:{line_item.model_description} line_description:{line_item.line_description}"
                )

    def _check_for_new_line_character(self, description):
        return self.NEW_LINE_CHARACTER in str(description)

    def _check_for_negative_price_for_model(self, line_item):
        self._check_for_net_and_gross_negative_price(
            "Model", line_item.gross_list_price, line_item.net_list_price
        )

    def _check_for_negative_price_for_options(self, line_item):
        for option in line_item.line_option_codes:
            self._check_for_net_and_gross_negative_price(
                "Option", option.gross_list_price, option.net_list_price
            )

    def _check_for_net_and_gross_negative_price(
        self, source, gross_list_price, net_list_price
    ):
        if self.vendor == Vendor.AUDI and self.market == Market.DE:
            return
        if float(gross_list_price) < 0:
            logger.warning(
                f"[{self.market}-{self.vendor}] {source} Negative Gross List Price"
            )
        if float(net_list_price) < 0:
            logger.warning(
                f"[{self.market}-{self.vendor}] {source} Negative Net List Price"
            )

    def _check_for_included_options_with_non_zero_price(self, line_item):
        for option in line_item.line_option_codes:
            if (
                option.included
                and option.gross_list_price != 0
                and (
                    self.vendor is Vendor.TESLA
                    or (self.vendor is Vendor.AUDI and self.market is not Market.US)
                    or self.vendor is Vendor.BMW
                )
            ):
                logger.warning(
                    f"[{self.market}-{self.vendor}] Option Included has Non-Zero Price for model_range:{line_item.model_range_description} model_description:{line_item.model_description} line_description:{line_item.line_description}"
                )

    def _check_for_model_duplication(self, line_items: list[LineItem]):
        line_item_list: list = []
        for line_item in line_items:
            model = (
                line_item.series
                + " # "
                + line_item.model_range_code
                + " # "
                + line_item.model_range_description
                + " # "
                + line_item.model_code
                + " # "
                + line_item.model_description
                + " # "
                + line_item.line_code
                + " # "
                + line_item.line_description
            )
            line_item_list.append(model)
        line_item_set = set(line_item_list)
        if len(line_item_set) != len(line_item_list):
            logger.warning(f"[{self.market}-{self.vendor}] Duplication of Models Found")
            logger.info(
                f"{[item for item, count in collections.Counter(line_item_list).items() if count > 1]}"
            )
