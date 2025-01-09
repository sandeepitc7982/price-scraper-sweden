from typing import List

import numpy as np
import pandas as pd
from loguru import logger

from src.price_monitor.data_quality.dq_dataclass import (
    QualityMetricsOutput,
    QualityRulesOutput,
)
from src.price_monitor.data_quality.dqutils import get_column_mapping


class BusinessInsights:
    def __init__(self, input_rules, input_parameters, config):
        self.config = config
        self.input_rules = input_rules
        self.input_parameters = input_parameters
        self.results: List[QualityMetricsOutput] = []
        self.failures: List[QualityRulesOutput] = []
        self.column_mapping = get_column_mapping()
        logger.debug(
            "Initialized BusinessInsights class with given input parameters and config."
        )

    def run_all_rules_metric(self):
        """
        Run all data quality checks and append results.
        """
        logger.debug("Running all data quality insights.")
        self.check_completeness(
            self.input_parameters,
            column="null_percentage",
            parameter="null_allowable",
            log_statement="Null",
        )
        self.check_completeness(
            self.input_parameters,
            column="zero_percentage",
            parameter="zero_allowable",
            log_statement="Zero",
        )
        self.check_completeness(
            self.input_parameters,
            column="special_char_percentage",
            parameter="special_char_allowable",
            log_statement="Special Character",
        )
        self.check_column_equality(self.input_parameters)
        self.check_data_type_consistency(self.input_parameters)
        self.check_range_and_validity(self.input_parameters)
        self.check_standard_deviation(self.input_parameters)
        logger.debug("Completed generating all data quality insights.")
        return self.results, self.failures

    def check_completeness(
        self, data: pd.DataFrame, column: str, parameter: str, log_statement: str
    ):
        """
        Perform null checks on each row of the DataFrame and append results to the self.results list.

        :param data: DataFrame with columns "column" and "null_percentage".
        :param column: The name of the column to be checked.
        :param parameter: the name of the cofig-file key to be obtained from config file
        :param log_statement: what is to be checked for eg. zero, null or special character
        """
        logger.debug(f"Starting {log_statement} completeness check.")
        acceptable_columns = self._get_acceptable_columns(
            parameter=parameter, log_statement=log_statement
        )
        overall_score, row_weight = self._initialize_scores(data, acceptable_columns)
        unique_vendor_str, unique_market_str = self._get_unique_vendor_market(data)

        for index, row in data.iterrows():
            column_name = row["column"]
            null_percentage = row[column]

            if column_name not in acceptable_columns:
                if null_percentage != 0:
                    logger.warning(
                        f"{log_statement} check failed for column: {column_name} with {null_percentage}% {log_statement}."
                    )
                    self.append_overall_failures(
                        unique_vendor_str,
                        unique_market_str,
                        overall_score=np.round(row_weight, 1),
                        insight=f"Column {column_name} may contain {null_percentage}% {log_statement} values",
                        metric="Completeness",
                        insight_type=f"{log_statement} check",
                        severity="High",
                    )
                    overall_score -= row_weight
                else:
                    logger.debug(
                        f"Column {column_name} passed {log_statement} check with 0% {log_statement}."
                    )

        self.append_overall_result(
            unique_vendor_str,
            unique_market_str,
            overall_score,
            insight=f"{log_statement} Check for all Columns",
            metric="Completeness",
            insight_type=f"{log_statement} check",
        )
        logger.debug(f"{log_statement} completeness check completed.")

    def check_column_equality(self, data: pd.DataFrame):
        logger.debug("Starting equality checks for specified column pairs")

        # Define the column pairs to check for equality
        checks = [
            (
                self.column_mapping["model_range_description"],
                self.column_mapping["model_range_code"],
            ),
            (
                self.column_mapping["monthly_rental_nlp"],
                self.column_mapping["monthly_rental_glp"],
            ),
            (self.column_mapping["fixed_roi"], self.column_mapping["apr"]),
        ]

        # Initialize variables
        total_checks = len(checks)
        passed_checks = 0
        unique_vendor_str, unique_market_str = self._get_unique_vendor_market(data)

        # Iterate through the checks
        for col1, col2 in checks:
            value1 = data.loc[data["column"] == col1, "distinct_count"].values
            value2 = data.loc[data["column"] == col2, "distinct_count"].values

            if value1.size == 0 or value2.size == 0:
                logger.warning(
                    f"Column {col1} or {col2} not found in the data or has no distinct counts."
                )
                self.append_overall_failures(
                    unique_vendor_str,
                    unique_market_str,
                    overall_score=0,
                    insight=f"Column {col1} or {col2} not found or no distinct counts available.",
                    metric="Validity",
                    insight_type="Equality check",
                    severity="High",  # Consider it a high severity issue since the column is missing
                )
                continue  # Skip this pair and move to the next
                # Now that we know values exist, we can safely access them
            value1 = value1[0]
            value2 = value2[0]

            if value1 == value2:
                passed_checks += 1
            else:
                logger.warning(
                    f"Distinct counts do not match for {col1} ({value1}) and {col2} ({value2})"
                )
                self.append_overall_failures(
                    unique_vendor_str,
                    unique_market_str,
                    overall_score=0,
                    insight=f"Distinct counts do not match for {col1} and {col2}",
                    metric="Validity",
                    insight_type="Equality check",
                    severity="Medium",
                )

        # Calculate the overall score
        overall_score = (passed_checks / total_checks) * 100

        if passed_checks == total_checks:
            insight_message = "All specified column pairs have equal distinct counts"
        else:
            insight_message = (
                "Some specified column pairs do not have equal distinct counts"
            )

        self.append_overall_result(
            unique_vendor_str,
            unique_market_str,
            overall_score,
            insight=insight_message,
            metric="Validity",
            insight_type="Equality check",
        )

    def check_data_type_consistency(self, data: pd.DataFrame):
        """
        Check that each row in the 'data_types' column contains only allowed data types
        as specified in the config. Append results and failures accordingly.

        :param data: DataFrame with columns 'column' and 'data_types', where 'data_types' contains
                     a list of data types for the column.
        """
        logger.debug("Starting data type consistency checks.")

        # Retrieve the required data type mapping and exclusion list from the config
        required_string_types = self.config["data_quality_finance"][
            "check_data_type_consistency"
        ]["data_type_requirements"]
        excluded_columns = set(
            self.config["data_quality_finance"]["check_data_type_consistency"][
                "data_type_exclusion"
            ]
        )

        # Filter the DataFrame to include only columns that are in the required types and not excluded
        columns_to_check = [
            col
            for col in data["column"].unique()
            if col in required_string_types and col not in excluded_columns
        ]

        if not columns_to_check:
            logger.debug("No columns to check based on the provided config.")
            return

        # Initialize variables for score calculation
        num_columns_to_check = len(columns_to_check)
        row_weight = 100.0 / num_columns_to_check
        overall_score = 100.0
        unique_vendor_str, unique_market_str = self._get_unique_vendor_market(data)

        # Iterate through each row in the DataFrame
        for index, row in data.iterrows():
            column_name = row["column"]
            data_type_list = row["data_types"]

            # Skip columns not in the list of columns to check
            if column_name not in columns_to_check:
                continue

            # Determine the expected types based on the column
            if column_name in required_string_types:
                allowed_types = ["String"]
            else:
                allowed_types = ["Integer", "Float"]

            # Check if all detected types are within the allowed types
            if all(detected_type in allowed_types for detected_type in data_type_list):
                logger.debug(
                    f"Column {column_name} passed data type consistency check with types: {data_type_list}."
                )
            else:
                # Identify any data types that are not allowed
                invalid_types = [t for t in data_type_list if t not in allowed_types]
                logger.warning(
                    f"Data type mismatch for column {column_name}. Allowed: {allowed_types}, "
                    f"Found: {data_type_list}. Invalid types: {invalid_types}."
                )
                self.append_overall_failures(
                    unique_vendor_str,
                    unique_market_str,
                    overall_score=np.round(row_weight, 1),
                    insight=f"Column {column_name} contains invalid types {invalid_types}. Expected: {allowed_types}, Found: {data_type_list}.",
                    metric="Consistency",
                    insight_type="Data Type Consistency check",
                    severity="High",
                )
                overall_score -= row_weight

        # Append the final overall result
        self.append_overall_result(
            unique_vendor_str,
            unique_market_str,
            overall_score,
            insight="Data Type Consistency Check for all Columns",
            metric="Consistency",
            insight_type="Data Type Consistency check",
        )
        logger.debug("Data type consistency checks completed.")

    def check_range_and_validity(self, data: pd.DataFrame):
        """
        Check if the column values in the data are within the specified range
        and validity as per the configuration. Log results and append failures if any.

        :param data: DataFrame with columns 'column', 'min', 'max', and 'vendor'.
        """
        logger.debug("Starting range and validity checks.")

        # Retrieve the tolerance and excluded columns from the config
        tolerance = self.config["data_quality_finance"]["range_and_non_negative_check"][
            "tolerance"
        ]
        excluded_columns = set(
            self.config["data_quality_finance"]["range_and_non_negative_check"][
                "excluded_columns"
            ]
        )
        vendor_ranges = self.config["data_quality_finance"][
            "range_and_non_negative_check"
        ]

        unique_vendor_str, unique_market_str = self._get_unique_vendor_market(data)
        # Initialize variables for score calculation
        columns_to_check = [
            col for col in data["column"].unique() if col not in excluded_columns
        ]
        num_columns_to_check = len(columns_to_check)
        if num_columns_to_check == 0:
            logger.debug("No columns to check based on the provided config.")
            return

        row_weight = 100.0 / num_columns_to_check
        overall_score = 100.0

        for index, row in data.iterrows():
            column_name = row["column"]
            min_value = row["min"]
            max_value = row["max"]
            vendor = row["vendor"]

            if column_name in excluded_columns:
                continue

            if vendor in vendor_ranges:
                # Get vendor-specific ranges
                vendor_config = vendor_ranges[vendor]
                if column_name in vendor_config:
                    ll = vendor_config[column_name]["ll"]
                    ul = vendor_config[column_name]["ul"]

                    # Check if min and max values are within the allowed range with tolerance
                    if not (
                        ll * (1 - tolerance / 100)
                        <= min_value
                        <= ul * (1 + tolerance / 100)
                        and ll * (1 - tolerance / 100)
                        <= max_value
                        <= ul * (1 + tolerance / 100)
                    ):
                        logger.warning(
                            f"Column {column_name} for vendor {vendor} is out of range. Min: {min_value}, "
                            f"Max: {max_value}, Expected LL: {ll}, UL: {ul}."
                        )
                        self.append_overall_failures(
                            unique_vendor_str,
                            unique_market_str,
                            overall_score=np.round(row_weight, 1),
                            insight=f"Column {column_name} for vendor {vendor} is out of range. Min: {min_value}, Max: {max_value}, Expected LL: {ll}, UL: {ul}.",
                            metric="Validity",
                            insight_type="Range Check",
                            severity="High",
                        )
                        overall_score -= row_weight
                else:
                    # Check non-range columns to be greater than zero
                    if min_value <= 0:
                        logger.warning(
                            f"Column {column_name} for vendor {vendor} has invalid minimum value. Min: {min_value}."
                        )
                        self.append_overall_failures(
                            unique_vendor_str,
                            unique_market_str,
                            overall_score=np.round(row_weight, 1),
                            insight=f"Column {column_name} for vendor {vendor} has invalid minimum value. Min: {min_value}.",
                            metric="Validity",
                            insight_type="Non-Negative Check",
                            severity="High",
                        )
                        overall_score -= row_weight
            # For vendors not in the config, do nothing

        # Append the final overall result
        self.append_overall_result(
            unique_vendor_str,
            unique_market_str,
            overall_score,
            insight="Range and Validity Check for all Columns",
            metric="Validity",
            insight_type="Range and Validity Check",
        )
        logger.debug("Range and validity checks completed.")

    def _get_acceptable_columns(self, parameter: str, log_statement: str) -> List[str]:
        """
        Extract the list of columns where nulls are acceptable from the config.
        """
        acceptable_columns = self.config["data_quality_finance"][
            "acceptable_columns_check"
        ]["field_requirements"][parameter]
        logger.debug(f"{log_statement} acceptable columns: {acceptable_columns}")
        return acceptable_columns

    def check_standard_deviation(self, data: pd.DataFrame):
        """
        Check if the standard deviation for each column in the data is within the specified tolerance
        and config settings for each vendor. Log results and append failures if any.

        :param data: DataFrame with columns 'column', 'std_dev', and 'vendor'.
        """
        logger.debug("Starting standard deviation checks.")

        # Retrieve the tolerance and excluded columns from the config
        tolerance = self.config["data_quality_finance"]["standard_dev_check"][
            "tolerance"
        ]
        excluded_columns = set(
            self.config["data_quality_finance"]["standard_dev_check"][
                "excluded_columns"
            ]
        )
        vendor_std_devs = self.config["data_quality_finance"]["standard_dev_check"]
        unique_vendor_str, unique_market_str = self._get_unique_vendor_market(data)
        # Initialize variables for score calculation
        overall_score = 100.0

        if unique_vendor_str not in vendor_std_devs:
            logger.debug(
                f"Vendor {unique_vendor_str} is not in the config. Skipping checks."
            )
            return

        vendor_columns = vendor_std_devs[unique_vendor_str].keys()
        columns_to_check = [
            col for col in vendor_columns if col not in excluded_columns
        ]
        num_columns_to_check = len(columns_to_check)

        if num_columns_to_check == 0:
            logger.debug("No columns to check based on the provided config.")
            return

        row_weight = 100.0 / num_columns_to_check

        for index, row in data.iterrows():
            column_name = row["column"]
            std_dev_value = row["std_dev"]
            vendor = row["vendor"]
            market = row["market"]

            if column_name in excluded_columns or column_name not in columns_to_check:
                continue

            config_std_dev = vendor_std_devs[vendor].get(column_name)

            # Check if the config standard deviation is zero
            if config_std_dev == 0:
                if std_dev_value != 0:
                    logger.warning(
                        f"Column {column_name} for vendor {vendor} has a non-zero standard deviation ({std_dev_value})"
                        f" when it should be zero."
                    )
                    self.append_overall_failures(
                        vendor,
                        market,
                        overall_score=np.round(row_weight, 1),
                        insight=f"Column {column_name} for vendor {vendor} has a non-zero standard deviation ({std_dev_value}) when it should be zero.",
                        metric="Accuracy",
                        insight_type="Standard Deviation Check",
                        severity="High",
                    )
                    overall_score -= row_weight
            else:
                # Check if the standard deviation is within the tolerance limit
                lower_bound = config_std_dev * (1 - tolerance / 100)
                upper_bound = config_std_dev * (1 + tolerance / 100)

                if not (lower_bound <= std_dev_value <= upper_bound):
                    logger.debug(
                        f"Column {column_name} for vendor {vendor} has an out-of-range standard deviation. "
                        f"Actual: {std_dev_value}, Expected: {config_std_dev} ± {tolerance}%."
                    )
                    self.append_overall_failures(
                        vendor,
                        market,
                        overall_score=np.round(row_weight, 1),
                        insight=f"Column {column_name} for vendor {vendor} has an out-of-range standard deviation. "
                        f"Actual: {std_dev_value}, Expected: {config_std_dev} ± {tolerance}%.",
                        metric="Accuracy",
                        insight_type="Standard Deviation Check",
                        severity="Medium",
                    )
                    overall_score -= row_weight

        # Append the final overall result
        self.append_overall_result(
            unique_vendor_str,
            unique_market_str,
            overall_score,
            insight="Standard Deviation Check for all Columns",
            metric="Accuracy",
            insight_type="Standard Deviation Check",
        )
        logger.debug("Standard deviation checks completed.")

    def _initialize_scores(
        self, data: pd.DataFrame, acceptable_columns: List[str]
    ) -> (float, float):
        """
        Initialize the overall score and row weight based on the data and acceptable columns.
        """
        num_rows = len(data)
        row_weight = 100.0 / (num_rows - len(acceptable_columns))
        overall_score = 100.0
        logger.debug(
            f"Initialized overall score: {overall_score}, row weight: {row_weight}."
        )
        return overall_score, row_weight

    def _get_unique_vendor_market(self, data: pd.DataFrame) -> (str, str):
        """
        Get unique vendor and market as comma-separated strings.
        """
        unique_vendor = data["vendor"].unique()
        unique_vendor_str = ", ".join(map(str, unique_vendor))
        unique_market = data["market"].unique()
        unique_market_str = ", ".join(map(str, unique_market))
        logger.debug(
            f"Unique vendors: {unique_vendor_str}, Unique markets: {unique_market_str}."
        )
        return unique_vendor_str, unique_market_str

    def append_overall_result(
        self,
        unique_vendor_str: str,
        unique_market_str: str,
        overall_score: float,
        insight: str,
        metric: str,
        insight_type: str,
    ):
        """
        Append the overall result after all rows have been checked.
        """
        logger.debug(f"Appending overall result with score: {overall_score}%.")
        self.results.append(
            QualityMetricsOutput(
                vendor=unique_vendor_str,
                market=unique_market_str,
                insight=insight,
                insight_type=insight_type,
                metric=metric,
                score=np.round(overall_score, 1),
            )
        )

    def append_overall_failures(
        self,
        unique_vendor_str: str,
        unique_market_str: str,
        overall_score: float,
        insight: str,
        metric: str,
        insight_type: str,
        severity: str,
    ):
        """
        Append the overall result after all rows have been checked.
        """
        logger.debug(f"Appending overall failures with score: {overall_score}%.")
        self.failures.append(
            QualityRulesOutput(
                vendor=unique_vendor_str,
                market=unique_market_str,
                insight=insight,
                insight_type=insight_type,
                metric=metric,
                score=np.round(overall_score, 1),
                severity=severity,
            )
        )
