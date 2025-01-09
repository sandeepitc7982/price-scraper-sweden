from dataclasses import asdict
from typing import List

import pandas as pd
from loguru import logger

from src.price_monitor.data_quality.business_rules import BusinessRules
from src.price_monitor.data_quality.datasampling import ScraperVerificationSample
from src.price_monitor.data_quality.dq_dataclass import (
    BusinessRulesReport,
    QualityMetricsOutput,
    QualityReport,
    QualityRulesOutput,
)
from src.price_monitor.data_quality.dqinsights import BusinessInsights
from src.price_monitor.data_quality.dqreport import DataQualityChecker
from src.price_monitor.data_quality.dqutils import (
    get_unique_identifier_column,
    save_output_file_to_directory,
)
from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.finance_item_repository import (
    FileSystemFinanceLineItemRepository,
)
from src.price_monitor.utils.clock import today_dashed_str_with_key


class FinanceDataQualityProcessor:
    """
    Processes financial data for multiple vendors and markets,
    performing data quality checks and business rule validations.
    The class consolidates results, generates reports, and handles sampling for visual verification.

    """

    def __init__(
        self, finance_line_item_repository: FileSystemFinanceLineItemRepository, config
    ):
        self.finance_line_item_repository = finance_line_item_repository
        self.market = ""
        self.vendor = ""
        self.config = config

    def run_quality_checks_all_vendors(self, config):
        vendor_markets_dict = config["finance_scraper"]["enabled"]
        df_combined = (
            []
        )  # create an empty list to combine the output dq results of each vendor and market
        df_sample_validation = (
            []
        )  # create an empty list to store samples for visual comparison from websites
        df_business_rules = (
            []
        )  # create an empty list to store business rules check outcome
        df_business_insights = []
        df_business_failures = []

        for vendor, markets in vendor_markets_dict.items():
            data, sample, rules = self.run_check_for_vendor_and_market(
                vendor=vendor, markets=markets
            )
            # Check if any of the returned values are None
            if data is None or sample is None or rules is None:
                logger.warning(
                    f"[{vendor}-{markets}] Skipping processing due to missing data."
                )
                continue  # Skip this iteration if any of the required data is missing

            self.append_and_save_output(data, df_combined, file_name="parameters")
            self.append_and_save_output(
                sample, df_sample_validation, file_name="sample_for_visual_comparison"
            )
            self.append_and_save_output(
                rules, df_business_rules, file_name="rules_output"
            )
            insight = BusinessInsights(
                input_rules=rules, input_parameters=data, config=self.config
            )
            insight_report, insight_failure = insight.run_all_rules_metric()
            self.append_and_save_output(
                insight_report, df_business_insights, file_name="insights_output"
            )
            if len(insight_failure) > 0:
                self.append_and_save_output(
                    insight_failure, df_business_failures, file_name="insights_failure"
                )

    def run_check_for_vendor_and_market(
        self, vendor: Vendor, markets: list[Market]
    ) -> (List[QualityReport], pd.DataFrame, List[BusinessRulesReport]):
        for market in markets:
            logger.info(f"Running data quality checks for {vendor}-{market}")
            finance_line_item_list = self.finance_line_item_repository.load_market(
                date=today_dashed_str_with_key(),
                market=market,
                vendor=vendor,
            )
            report, sample, rules = self.assert_output(
                finance_line_items=finance_line_item_list,
                market=market,
                vendor=vendor,
            )
            return report, sample, rules

    def assert_output(
        self,
        finance_line_items: list[FinanceLineItem],
        market: Market,
        vendor: Vendor,
    ):
        if len(finance_line_items) == 0:
            logger.warning(f"[{self.market}-{self.vendor}] Zero Models Found")
            return None, None, None
        else:
            logger.info(f"[{self.market}--{self.vendor}] data fetched successfully")
            # Preprocess the data before running data quality checks
            df = self._preprocess(finance_line_items)
            quality_report = DataQualityChecker(
                vendor=vendor, market=market, config=self.config
            )
            output = quality_report.run_all_checks(df)
            # Adding business rules code run below:
            businessrules = BusinessRules(df, self.config, vendor, market)
            rules_output = businessrules.run_all_business_rules()

            # Initialize ScraperVerificationSample class with DataFrame and config
            verifier = ScraperVerificationSample(df, self.config)
            # Generate the sample for verification
            sample_df = verifier.generate_sample()

            return output, sample_df, rules_output

    def _preprocess(
        self, finance_line_items_in_market: list[FinanceLineItem]
    ) -> pd.DataFrame:
        """
        Preprocess the finance line items by converting them into a DataFrame,
        creating a unique identifier column, and filtering the data based on the 'PCP' contract type.

        Args:
            finance_line_items_in_market (list[FinanceLineItem]): List of finance line items for a specific market.

        Returns:
            pd.DataFrame: Preprocessed DataFrame ready for data quality checks.
        """
        # Convert the list of finance line items into a DataFrame
        df = pd.DataFrame(finance_line_items_in_market)

        # Create a column for unique car line
        df = get_unique_identifier_column(df)

        # Filter the data for "PCP" if the field is None no filter will be applied
        df = self.filter_data_pcp(df)

        return df

    def filter_data_pcp(self, data):
        # Filter the data for "PCP" if the field is None no filter will be applied
        contract_type = self.config["data_quality_finance"]["contract_type"]
        if contract_type == "PCP":
            data = data[data["contract_type"].str.contains(contract_type)]
            logger.info(
                f"[{self.market}--{self.vendor}] data filtered for {contract_type} contract_type"
            )
        else:
            logger.info(
                f"[{self.market}--{self.vendor}] data not filtered by contract_type"
            )
        return data

    def append_and_save_output(self, data, list_name, file_name):
        if all(isinstance(item, BusinessRulesReport) for item in data):
            data = pd.DataFrame([asdict(report) for report in data])
        elif all(isinstance(item, QualityReport) for item in data):
            data = pd.DataFrame([asdict(report) for report in data])
        elif all(isinstance(item, QualityMetricsOutput) for item in data):
            data = pd.DataFrame([asdict(report) for report in data])
        elif all(isinstance(item, QualityRulesOutput) for item in data):
            data = pd.DataFrame([asdict(report) for report in data])
        list_name.append(data)
        report = pd.concat(list_name, ignore_index=True)
        save_output_file_to_directory(self.config, report, file_name)
