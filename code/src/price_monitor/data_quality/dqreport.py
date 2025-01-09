import numpy as np
import pandas as pd
from loguru import logger

from src.price_monitor.data_quality.dq_dataclass import QualityReportOutput
from src.price_monitor.utils.clock import (
    today_dashed_str,
    current_timestamp_dashed_str_with_timezone,
)


class DataQualityChecker:
    def __init__(self, vendor: str, market: str, config):
        self.vendor = vendor
        self.market = market
        self.config = config
        self.recorded_at = current_timestamp_dashed_str_with_timezone()
        logger.debug(
            f"Initialized DataQualityChecker for vendor: {vendor}, market: {market}"
        )

    def run_all_checks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run all data quality checks and return the results in a DataFrame.
        """
        results = []

        for column in df.columns:
            column_results = self._check_column(df[column], column)
            results.append(column_results)
            if column == "last_scraped_on":
                df_scraper_check = df[
                    (
                        df["last_scraped_on"] != today_dashed_str()
                    )  # Filter out rows matching the date
                    & (df["last_scraped_on"] != "0")
                ]  # Exclude zero values]
                if len(df_scraper_check) > 0:
                    logger.warning(
                        f"Column '{column}' has date value scraped from previous date/s"
                    )
                column_results = self._check_column(
                    df_scraper_check[column], column + "_is_false"
                )
                results.append(column_results)
        # Assuming 'results' is your list of dictionaries
        filtered_results = [res for res in results if res is not None]

        # Optional: Log the indices of None values (for debugging purposes)
        none_indices = [index for index, res in enumerate(results) if res is None]
        if none_indices:
            logger.warning(f"Found None at indices: {none_indices}")

        # Now convert the filtered list to a DataFrame
        results_df = pd.DataFrame(filtered_results)
        # results_df = pd.DataFrame(results)
        logger.debug("Data quality checks completed successfully.")
        return results_df

    def _check_column(self, series: pd.Series, column_name: str) -> dict:
        """
        Perform data quality checks on a single column and return the results as a dictionary.
        """
        # Attempt to convert series to numeric and handle conversion warnings
        numeric_columns = self.config["data_quality_finance"]["numeric_columns"]
        if series.name in numeric_columns:
            numeric_series = pd.to_numeric(series, errors="coerce")
            if numeric_series.notna().sum() < len(series):
                logger.warning(
                    f"Column '{column_name}' has non-numeric values that could not be converted."
                )
            report = self._is_numeric(numeric_series, series, column_name)
            result = self._calculations(series, column_name, report)
            return result
        else:
            report = self._is_non_numeric(series)
            result = self._calculations(series, column_name, report)
            return result

    def _is_numeric(self, numeric_series, series, column_name) -> QualityReportOutput:
        total_count = len(numeric_series)
        null_count = numeric_series.isnull().sum() + (series == "").sum()
        zero_count = (numeric_series == 0).sum()

        # Remove null, blank, and zero values from the series for distinct calculations
        filtered_series = numeric_series[
            ~numeric_series.isnull() & (numeric_series != "") & (numeric_series != 0)
        ]

        # Calculate distinct and non-distinct counts excluding nulls, blanks, and zeros
        distinct_count = filtered_series.nunique()
        filtered_count = len(filtered_series)  # Count after filtering

        # Calculate non-distinct count (remaining non-null, non-zero, non-blank after removing distinct)
        non_distinct_count = filtered_count - distinct_count

        # Check for data type consistency for a numeric column
        unique_types = {
            self.map_to_general_type(value)
            for value in numeric_series.dropna().unique()
        }

        # Filter out zeros for numeric calculations
        filtered_numeric_series = numeric_series[numeric_series != 0]

        # For numeric columns, calculate statistics without zeros and nulls
        mean_value = self.round_to_two_decimals(filtered_numeric_series.mean())
        min_value = self.round_to_two_decimals(filtered_numeric_series.min())
        max_value = self.round_to_two_decimals(filtered_numeric_series.max())
        percentile_25 = self.round_to_two_decimals(
            filtered_numeric_series.quantile(0.25)
        )
        percentile_50 = self.round_to_two_decimals(
            filtered_numeric_series.quantile(0.50)
        )
        percentile_75 = self.round_to_two_decimals(
            filtered_numeric_series.quantile(0.75)
        )
        std_dev = self.round_to_two_decimals(filtered_numeric_series.std())
        inconsistent_type = len(unique_types) > 1

        if min_value < 0:
            logger.warning(
                f"Column '{column_name}' has negative values that could impact data quality"
            )
        if inconsistent_type:
            logger.warning(
                f"Column '{column_name}' is inconsistent with types: {unique_types}"
            )
        else:
            logger.debug(
                f"Column '{column_name}' is consistent with type: {unique_types}"
            )

        return QualityReportOutput(
            total_count=total_count,
            null_count=null_count,
            zero_count=zero_count,
            distinct_count=distinct_count,
            non_distinct_count=non_distinct_count,
            mean_value=mean_value,
            min_value=min_value,
            max_value=max_value,
            percentile_25=percentile_25,
            percentile_50=percentile_50,
            percentile_75=percentile_75,
            std_dev=std_dev,
            unique_types=list(unique_types),
            inconsistent_type=inconsistent_type,
        )

    def _is_non_numeric(self, series) -> QualityReportOutput:
        total_count = len(series)
        null_count = series.isnull().sum() + (series == "").sum()
        zero_count = (series == 0).sum()

        # Remove null, blank, and zero values from the series for distinct calculations
        filtered_series = series[~series.isnull() & (series != "") & (series != 0)]

        # Calculate distinct and non-distinct counts excluding nulls, blanks, and zeros
        distinct_count = filtered_series.nunique()
        filtered_count = len(filtered_series)  # Count after filtering

        # Calculate non-distinct count (remaining non-null, non-zero, non-blank after removing distinct)
        non_distinct_count = filtered_count - distinct_count
        # For string columns, calculate statistics based on the length of the strings
        length_series = series.astype(str).apply(len)
        mean_value = self.round_to_two_decimals(length_series.mean())
        min_value = self.round_to_two_decimals(length_series.min())
        max_value = self.round_to_two_decimals(length_series.max())
        percentile_25 = self.round_to_two_decimals(length_series.quantile(0.25))
        percentile_50 = self.round_to_two_decimals(length_series.quantile(0.50))
        percentile_75 = self.round_to_two_decimals(length_series.quantile(0.75))
        std_dev = self.round_to_two_decimals(length_series.std())

        # Check for data type consistency if not a string column
        unique_types = {
            self.map_to_general_type(value) for value in series.dropna().unique()
        }
        inconsistent_type = len(unique_types) > 1
        if inconsistent_type:
            logger.warning(
                f"Column '{series.name}' is inconsistent with types: {unique_types}"
            )
        else:
            logger.debug(
                f"Column '{series.name}' is consistent with type: {unique_types}"
            )
        return QualityReportOutput(
            total_count=total_count,
            null_count=null_count,
            zero_count=zero_count,
            distinct_count=distinct_count,
            non_distinct_count=non_distinct_count,
            mean_value=mean_value,
            min_value=min_value,
            max_value=max_value,
            percentile_25=percentile_25,
            percentile_50=percentile_50,
            percentile_75=percentile_75,
            std_dev=std_dev,
            unique_types=list(unique_types),
            inconsistent_type=inconsistent_type,
        )

    def _calculations(self, series, column_name, report):
        # Calculate percentages
        null_percentage = self.round_to_two_decimals(
            (report.null_count / report.total_count) * 100
            if report.total_count > 0
            else 0
        )
        if null_percentage > 0:
            logger.debug(f"Column '{column_name}' has '{null_percentage}'% null values")
        zero_percentage = self.round_to_two_decimals(
            (report.zero_count / report.total_count) * 100
            if report.total_count > 0
            else 0
        )
        if zero_percentage > 0:
            logger.debug(f"Column '{column_name}' has '{zero_percentage}'% zero values")
        distinct_percentage = self.round_to_two_decimals(
            (report.distinct_count / report.total_count) * 100
            if report.total_count > 0
            else 0
        )
        non_distinct_percentage = self.round_to_two_decimals(
            (report.non_distinct_count / report.total_count) * 100
            if report.total_count > 0
            else 0
        )

        # Special character check
        special_characters = ["\n", ":", "'", '"', ",", ";", "√", "©"]
        special_char_count = sum(
            series.apply(lambda x: any(char in str(x) for char in special_characters))
        )
        special_char_percentage = self.round_to_two_decimals(
            (special_char_count / report.total_count) * 100
            if report.total_count > 0
            else 0
        )
        if special_char_percentage > 0:
            logger.debug(
                f"Column '{column_name}' has '{special_char_percentage}'% special character present"
            )
        if special_char_count > 0:
            logger.debug(
                f"Column '{column_name}' contains special characters in {special_char_count} rows."
            )
        result = {
            "vendor": self.vendor,
            "market": self.market,
            "column": column_name,
            "total_row_count": report.total_count,
            "null_count": report.null_count,
            "null_percentage": null_percentage,
            "distinct_count": report.distinct_count,
            "distinct_percentage": distinct_percentage,
            "non_distinct_count": report.non_distinct_count,
            "non_distinct_percentage": non_distinct_percentage,
            "zero_count": report.zero_count,
            "zero_percentage": zero_percentage,
            "data_types": list(report.unique_types),
            "special_char_count": special_char_count,
            "special_char_percentage": special_char_percentage,
            "mean": report.mean_value,
            "min": report.min_value,
            "max": report.max_value,
            "25_percentile": report.percentile_25,
            "50_percentile": report.percentile_50,
            "75_percentile": report.percentile_75,
            "std_dev": report.std_dev,
        }
        return result

    # Map data types to more general categories
    def map_to_general_type(self, value) -> str:
        # Check for specific numpy types first
        if isinstance(value, (np.integer, int)):
            return "Integer"
        elif isinstance(value, (np.floating, float)):
            return "Float"
        elif isinstance(value, (np.str_, str)):
            try:
                float_value = float(value)
                if float_value.is_integer():
                    return "Integer"
                return "Float"
            except ValueError:
                return "String"
        elif isinstance(value, (np.bool_, bool)):
            return "Boolean"
        else:
            return "Unknown"

    def round_to_two_decimals(self, value):
        if isinstance(value, list):
            return [round(num, 2) for num in value]
        else:
            return round(value, 2)
