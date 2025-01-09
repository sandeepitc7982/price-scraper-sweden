import collections

from loguru import logger

from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.finance_item_repository import (
    FileSystemFinanceLineItemRepository,
)
from src.price_monitor.utils.clock import today_dashed_str_with_key


class DataQualityCheckFinance:
    def __init__(
        self, finance_line_item_repository: FileSystemFinanceLineItemRepository
    ):
        self.finance_line_item_repository = finance_line_item_repository
        self.NEW_LINE_CHARACTER = "\n"
        self.market = ""
        self.vendor = ""

    def run_quality_checks_all_vendors(self, config):
        vendor_markets_dict = config["finance_scraper"]["enabled"]

        for vendor, markets in vendor_markets_dict.items():
            self.run_check_for_vendor_and_market(vendor=vendor, markets=markets)

    def run_check_for_vendor_and_market(self, vendor: Vendor, markets: list[Market]):
        for market in markets:
            logger.info(f"Running data quality checks for {vendor}-{market}")
            finance_line_item_list = self.finance_line_item_repository.load_market(
                date=today_dashed_str_with_key(),
                market=market,
                vendor=vendor,
            )
            self.market = market
            self.vendor = vendor
            self.assert_output(finance_line_items=finance_line_item_list, market=market)

    def assert_output(self, finance_line_items: list[FinanceLineItem], market: Market):
        finance_line_items_in_market = list(
            filter(lambda item: (item.market == market), finance_line_items)
        )
        if len(finance_line_items_in_market) == 0:
            logger.warning(f"[{self.market}-{self.vendor}] Zero Models Found")
        else:
            self._check_for_model_duplication(finance_line_items)
            for finance_line_item in finance_line_items_in_market:
                self._check_for_negative_price_for_line(finance_line_item)
                self._check_for_new_line_character_in_descriptions(finance_line_item)

                if "PCP" in finance_line_item.contract_type:
                    self._check_for_number_of_instalments_higher_than_zero(
                        finance_line_item
                    )
                    self._check_for_no_of_installments_not_higher_than_contract_duration(
                        finance_line_item
                    )

    def _check_for_new_line_character_in_descriptions(self, finance_line_item):
        if self._check_for_new_line_character(
            finance_line_item.model_range_description
        ):
            logger.warning(
                f"[{self.market}-{self.vendor}] New Line Character Error in Model_Range_Description for model_range:{finance_line_item.model_range_description} model_description:{finance_line_item.model_description} line_description:{finance_line_item.line_description}"
            )
        if self._check_for_new_line_character(finance_line_item.model_description):
            logger.warning(
                f"[{self.market}-{self.vendor}] New Line Character Error in Model_Description for model_range:{finance_line_item.model_range_description} model_description:{finance_line_item.model_description} line_description:{finance_line_item.line_description}"
            )
        if self._check_for_new_line_character(finance_line_item.line_description):
            logger.warning(
                f"[{self.market}-{self.vendor}] New Line Character Error in Line_Description for model_range:{finance_line_item.model_range_description} model_description:{finance_line_item.model_description} line_description:{finance_line_item.line_description}"
            )

    def _check_for_new_line_character(self, description):
        return self.NEW_LINE_CHARACTER in str(description)

    def _check_for_negative_price_for_line(self, finance_line_item: FinanceLineItem):
        if float(finance_line_item.monthly_rental_glp) < 0:
            logger.warning(
                f"[{self.market}-{self.vendor}] Negative Monthly Rental GLP for model_range:{finance_line_item.model_range_description} model_description:{finance_line_item.model_description} line_description:{finance_line_item.line_description}"
            )
        if float(finance_line_item.monthly_rental_nlp) < 0:
            logger.warning(
                f"[{self.market}-{self.vendor}] Negative Monthly Rental NLP for model_range:{finance_line_item.model_range_description} model_description:{finance_line_item.model_description} line_description:{finance_line_item.line_description}"
            )

    def _check_for_model_duplication(self, finance_line_items: list[FinanceLineItem]):
        finance_line_item_list: list = []
        for finance_line_item in finance_line_items:
            model = (
                finance_line_item.series
                + " # "
                + finance_line_item.model_range_code
                + " # "
                + finance_line_item.model_range_description
                + " # "
                + finance_line_item.model_code
                + " # "
                + finance_line_item.model_description
                + " # "
                + finance_line_item.line_code
                + " # "
                + finance_line_item.line_description
                + " # "
                + finance_line_item.contract_type
            )
            finance_line_item_list.append(model)
        finance_line_item_set = set(finance_line_item_list)
        if len(finance_line_item_set) != len(finance_line_item_list):
            logger.warning(f"[{self.market}-{self.vendor}] Duplication of Models Found")
            for item, count in collections.Counter(finance_line_item_list).items():
                if count > 1:
                    logger.warning(f"{item}\n")

    def _check_for_number_of_instalments_higher_than_zero(
        self, finance_line_item: FinanceLineItem
    ):
        if finance_line_item.number_of_installments <= 0:
            logger.warning(
                f"[{self.market}-{self.vendor}] No. of Installments Zero for model_range:{finance_line_item.model_range_description} model_description:{finance_line_item.model_description} line_description:{finance_line_item.line_description}"
            )

    def _check_for_no_of_installments_not_higher_than_contract_duration(
        self, finance_line_item: FinanceLineItem
    ):
        # typecasted to int as we changed term_of_agreement datatype to integer
        if (
            int(finance_line_item.term_of_agreement)
            < finance_line_item.number_of_installments
        ):
            logger.warning(
                f"[{self.market}-{self.vendor}] No. of installments is greater then contract duration for model_range:{finance_line_item.model_range_description} model_description:{finance_line_item.model_description} line_description:{finance_line_item.line_description}"
            )
