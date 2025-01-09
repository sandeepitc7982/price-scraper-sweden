from typing import List

import pandas as pd
from loguru import logger

from src.price_monitor.data_quality.dqutils import (
    BusinessRulesReport,
    get_unique_identifier_column,
    get_column_mapping,
    iterate_df_append_rules,
)


class BusinessRules:
    def __init__(self, input_data, config, vendor, market):
        self.config = config
        self.input_data = input_data
        self.results: List[BusinessRulesReport] = []
        self.vendor = vendor
        self.market = market
        self.column_mapping = get_column_mapping()

    def run_all_business_rules(self):
        data = self._convert_columns_to_numeric(self.input_data)
        self.check_glp_greater_than_nlp(data)
        self.check_total_payable_greater_than_otr(data)
        self.check_no_duplicate_records(data)
        self.check_duplicates_unique_line(data)
        self.check_total_deposit_greater_than_deposit(data)
        self.check_total_deposit_and_credit_equals_to_otr(data)
        self.check_optional_payment_less_than_total_payable(data)
        self.fixed_roi_less_than_apr(data)
        self.check_vendor_series_correctness(data)
        self.check_currency_unit_correctness(data)
        self.check_optional_payment_less_than_otr(data)
        return self.results

    def check_glp_greater_than_nlp(self, dataframe: pd.DataFrame):
        required_columns = {
            self.column_mapping["monthly_rental_glp"],
            self.column_mapping["monthly_rental_nlp"],
            self.column_mapping["vendor"],
            self.column_mapping["market"],
        }
        if not check_required_columns(dataframe, required_columns):
            return  # Skip the rule if required columns are missing

        def rule_function(row, column_mapping):
            glp = row[column_mapping["monthly_rental_glp"]]
            nlp = row[column_mapping["monthly_rental_nlp"]]
            return glp > nlp

        apply_rule_to_dataframe(
            dataframe=dataframe,
            column_mapping=self.column_mapping,
            rule_name="GLP Amount greater than NLP",
            rule_function=rule_function,
            input_data=self.input_data,
            results=self.results,
            vendor=self.vendor,
            market=self.market,
            rule_columns=["monthly_rental_glp", "monthly_rental_nlp"],
        )

    def check_total_payable_greater_than_otr(self, dataframe: pd.DataFrame):
        required_columns = {
            self.column_mapping["total_payable_amount"],
            self.column_mapping["otr"],
            self.column_mapping["vendor"],
            self.column_mapping["market"],
        }
        if not check_required_columns(dataframe, required_columns):
            return  # Skip the rule if required columns are missing

        def rule_function(row, column_mapping):
            total_payable = row[column_mapping["total_payable_amount"]]
            otr = row[column_mapping["otr"]]
            return total_payable > otr

        apply_rule_to_dataframe(
            dataframe=dataframe,
            column_mapping=self.column_mapping,
            rule_name="Total Payable Amount greater than OTR",
            rule_function=rule_function,
            input_data=self.input_data,
            results=self.results,
            vendor=self.vendor,
            market=self.market,
            rule_columns=["total_payable_amount", "otr"],
        )

    def check_no_duplicate_records(self, dataframe: pd.DataFrame):
        total_rows = len(dataframe)
        duplicate_rows = dataframe.duplicated(keep=False).sum()

        if duplicate_rows > 0:
            logger.warning(
                f"[{self.market}-{self.vendor}] Found {duplicate_rows} duplicate records in the data."
            )

        duplicate_percentage = (
            ((total_rows - duplicate_rows) / total_rows) * 100 if total_rows > 0 else 0
        )
        iterate_df_append_rules(
            input_data=self.input_data,
            rule_name="Duplicate Records",
            column_name="All Columns",
            success_percentage=duplicate_percentage,
            results=self.results,
            vendor=self.vendor,
            market=self.market,
        )

    def check_duplicates_unique_line(self, dataframe: pd.DataFrame):
        data = get_unique_identifier_column(dataframe)
        required_columns = {self.column_mapping["unique_car_line"]}
        if not check_required_columns(dataframe, required_columns):
            return  # Skip the rule if required columns are missing

        subset_df = data[[self.column_mapping["unique_car_line"]]].copy()
        total_rows = len(subset_df)
        duplicate_rows = subset_df.duplicated(keep=False).sum()

        if duplicate_rows > 0:
            logger.warning(
                f"[{self.market}-{self.vendor}] Found {duplicate_rows} duplicate car line in the data."
            )

        duplicate_percentage = (
            ((total_rows - duplicate_rows) / total_rows) * 100 if total_rows > 0 else 0
        )
        iterate_df_append_rules(
            input_data=self.input_data,
            rule_name="Duplicate Car line Records",
            column_name="Unique line combining series, model range, model code, line code and contract type",
            success_percentage=duplicate_percentage,
            results=self.results,
            vendor=self.vendor,
            market=self.market,
        )

    def check_total_deposit_greater_than_deposit(self, dataframe: pd.DataFrame):
        required_columns = {
            self.column_mapping["total_deposit"],
            self.column_mapping["deposit"],
            self.column_mapping["vendor"],
            self.column_mapping["market"],
        }
        if not check_required_columns(dataframe, required_columns):
            return  # Skip the rule if required columns are missing

        def rule_function(row, column_mapping):
            total_deposit = row[column_mapping["total_deposit"]]
            deposit = row[column_mapping["deposit"]]
            return total_deposit >= deposit

        apply_rule_to_dataframe(
            dataframe=dataframe,
            column_mapping=self.column_mapping,
            rule_name="Total Deposit greater than or equal to Deposit",
            rule_function=rule_function,
            input_data=self.input_data,
            results=self.results,
            vendor=self.vendor,
            market=self.market,
            rule_columns=["total_deposit", "deposit"],
        )

    def check_total_deposit_and_credit_equals_to_otr(self, dataframe: pd.DataFrame):
        required_columns = {
            self.column_mapping["total_deposit"],
            self.column_mapping["total_credit_amount"],
            self.column_mapping["otr"],
            self.column_mapping["vendor"],
            self.column_mapping["market"],
        }
        if not check_required_columns(dataframe, required_columns):
            return  # Skip the rule if required columns are missing

        def rule_function(row, column_mapping):
            total_deposit = row[column_mapping["total_deposit"]]
            total_credit = row[column_mapping["total_credit_amount"]]
            otr = row[column_mapping["otr"]]
            return (total_deposit + total_credit) == otr

        apply_rule_to_dataframe(
            dataframe=dataframe,
            column_mapping=self.column_mapping,
            rule_name="Total Deposit and Total credit added equals to OTR",
            rule_function=rule_function,
            input_data=self.input_data,
            results=self.results,
            vendor=self.vendor,
            market=self.market,
            rule_columns=["total_deposit", "total_credit_amount", "otr"],
        )

    def fixed_roi_less_than_apr(self, dataframe: pd.DataFrame):
        required_columns = {
            self.column_mapping["fixed_roi"],
            self.column_mapping["apr"],
            self.column_mapping["deposit"],
            self.column_mapping["vendor"],
            self.column_mapping["market"],
        }
        if not check_required_columns(dataframe, required_columns):
            return  # Skip the rule if required columns are missing

        def rule_function(row, column_mapping):
            deposit = row[column_mapping["deposit"]]
            fixed_roi = row[column_mapping["fixed_roi"]]
            apr = row[column_mapping["apr"]]
            if deposit == 0:
                return fixed_roi < apr
            else:
                return (fixed_roi >= apr) or (fixed_roi < apr)

        apply_rule_to_dataframe(
            dataframe=dataframe,
            column_mapping=self.column_mapping,
            rule_name="Fixed ROI is less than or equal to APR",
            rule_function=rule_function,
            input_data=self.input_data,
            results=self.results,
            vendor=self.vendor,
            market=self.market,
            rule_columns=["deposit", "fixed_roi", "apr"],
        )

    def check_optional_payment_less_than_total_payable(self, dataframe: pd.DataFrame):
        required_columns = {
            self.column_mapping["optional_final_payment"],
            self.column_mapping["total_payable_amount"],
            self.column_mapping["vendor"],
            self.column_mapping["market"],
        }
        if not check_required_columns(dataframe, required_columns):
            return  # Skip the rule if required columns are missing

        def rule_function(row, column_mapping):
            optional_payment = row[column_mapping["optional_final_payment"]]
            total_payment = row[column_mapping["total_payable_amount"]]
            return optional_payment < total_payment

        apply_rule_to_dataframe(
            dataframe=dataframe,
            column_mapping=self.column_mapping,
            rule_name="Optional payment less than total payable amount",
            rule_function=rule_function,
            input_data=self.input_data,
            results=self.results,
            vendor=self.vendor,
            market=self.market,
            rule_columns=["optional_final_payment", "total_payable_amount"],
        )

    def check_optional_payment_less_than_otr(self, dataframe: pd.DataFrame):
        required_columns = {
            self.column_mapping["optional_final_payment"],
            self.column_mapping["otr"],
            self.column_mapping["vendor"],
            self.column_mapping["market"],
        }
        if not check_required_columns(dataframe, required_columns):
            return  # Skip the rule if required columns are missing

        def rule_function(row, column_mapping):
            optional_payment = row[column_mapping["optional_final_payment"]]
            otr = row[column_mapping["otr"]]
            return optional_payment < otr

        apply_rule_to_dataframe(
            dataframe=dataframe,
            column_mapping=self.column_mapping,
            rule_name="Optional payment less than otr",
            rule_function=rule_function,
            input_data=self.input_data,
            results=self.results,
            vendor=self.vendor,
            market=self.market,
            rule_columns=["optional_final_payment", "otr"],
        )

    def check_vendor_series_correctness(self, dataframe: pd.DataFrame):
        required_columns = {
            self.column_mapping["series"],
            self.column_mapping["vendor"],
            self.column_mapping["market"],
        }

        if not check_required_columns(dataframe, required_columns):
            return  # Skip the rule if required columns are missing

        def rule_function(data):
            if self.vendor == "audi":
                audi_series = self.config["data_quality_finance"]["audi_series"]
                audi_series_data = data[self.column_mapping["series"]].tolist()
                match_percentage = calculate_match_percentage(
                    audi_series, audi_series_data
                )
            elif self.vendor == "bmw":
                bmw_series = self.config["data_quality_finance"]["bmw_series"]
                bmw_series_data = data[self.column_mapping["series"]].unique().tolist()
                match_percentage = calculate_match_percentage(
                    bmw_series, bmw_series_data
                )
            elif self.vendor == "tesla":
                tesla_series = self.config["data_quality_finance"]["tesla_series"]
                tesla_series_data = (
                    data[self.column_mapping["series"]].unique().tolist()
                )
                match_percentage = calculate_match_percentage(
                    tesla_series, tesla_series_data
                )
            else:
                match_percentage = 0
            return match_percentage

        match_percentage = rule_function(dataframe)

        iterate_df_append_rules(
            input_data=self.input_data,
            rule_name="Match vendor series with standard series records",
            column_name="series and config parameters",
            success_percentage=match_percentage,
            results=self.results,
            vendor=self.vendor,
            market=self.market,
        )

    def check_currency_unit_correctness(self, dataframe: pd.DataFrame):
        required_columns = {
            self.column_mapping["currency"],
            self.column_mapping["vendor"],
            self.column_mapping["market"],
        }

        if not check_required_columns(dataframe, required_columns):
            return  # Skip the rule if required columns are missing

        def rule_function(data):
            if data[self.column_mapping["market"]].isin(["UK"]).any():
                currency = [self.config["data_quality_finance"]["currency"]["UK"]]
                currency_series = data[self.column_mapping["currency"]].tolist()
                match_percentage = calculate_match_percentage(currency, currency_series)
            else:
                return
            return match_percentage

        match_percentage = rule_function(dataframe)

        iterate_df_append_rules(
            input_data=self.input_data,
            rule_name="Match currency with market currency",
            column_name="currency and config parameters for currency",
            success_percentage=match_percentage,
            results=self.results,
            vendor=self.vendor,
            market=self.market,
        )

    def _convert_columns_to_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts each column in the DataFrame to numeric, if possible.
        String and boolean columns are kept unchanged.

        :param df: The input DataFrame.
        :return: The processed DataFrame with numeric conversions applied.
        """

        def convert_column(col):
            numeric_columns = self.config["data_quality_finance"]["numeric_columns"]
            if col.name in numeric_columns:
                # Attempt to convert the column to numeric
                return pd.to_numeric(col, errors="coerce")
            else:
                return col  # Return the column unchanged if conversion fails

        # Apply the conversion to each column
        df_converted = df.apply(convert_column)

        return df_converted


def check_required_columns(dataframe: pd.DataFrame, required_columns: set) -> bool:
    """
    Checks if all required columns are present in the DataFrame: dataframe: The DataFrame to check.
    :param required_columns: A set of column names that are required.
    :return: True if all required columns are present, False otherwise.
    """
    missing_columns = required_columns - set(dataframe.columns)
    if missing_columns:
        logger.warning(
            f"DataFrame is missing required columns: {', '.join(missing_columns)}"
        )
        return False
    return True


def apply_rule_to_dataframe(
    dataframe: pd.DataFrame,
    column_mapping: dict,
    rule_name: str,
    rule_function: callable,
    input_data,
    results: list,
    vendor: str,
    market: str,
    rule_columns: list,
) -> None:
    """
    Iterates through the DataFrame and applies a given rule.
    :param dataframe: The DataFrame to process.
    :param column_mapping: A dictionary mapping logical column names to actual column names.
    :param rule_name: The name of the rule being applied.
    :param rule_function: A callable that applies the rule logic to a row.
    :param input_data: Input data used for appending rule results.
    :param results: A list where rule results are appended.
    :param vendor: The vendor name.
    :param market: The market name.
    """
    total_rows = len(dataframe)
    violations = 0

    for index, row in dataframe.iterrows():
        if not rule_function(row, column_mapping):
            violations += 1
            logger.warning(
                f"[{market}-{vendor}] Rule '{rule_name}' violated at row {index}."
            )

    success_percentage = (
        ((total_rows - violations) / total_rows) * 100 if total_rows > 0 else 0
    )
    # Use only the specified columns in the column_name
    columns_used = ", ".join([column_mapping[col] for col in rule_columns])
    iterate_df_append_rules(
        input_data=input_data,
        rule_name=rule_name,
        column_name=columns_used,
        success_percentage=success_percentage,
        results=results,
        vendor=vendor,
        market=market,
    )


def calculate_match_percentage(config_series, series_data):
    """
    Calculate the match percentage between the config series and the actual series data.

    :param config_series: List of expected series from the config.
    :param series_data: List of actual series from the data.
    :return: Match percentage as a float.
    """
    # Check if all series_data items are in config_series
    missing_items = [item for item in series_data if item not in config_series]
    if not missing_items:
        return 100.0  # All items in series_data are present in config_series
        # Log items that are out of scope
    for item in missing_items:
        logger.warning(
            f"'{item}' is not present in the config series and is out of scope."
        )

    # Calculate match percentage for items that are in the config_series
    matching_items = len(series_data) - len(missing_items)
    total_items = len(series_data)

    match_percentage = (matching_items / total_items) * 100
    return match_percentage
