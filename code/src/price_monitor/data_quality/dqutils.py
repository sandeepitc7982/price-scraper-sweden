import pandas as pd
from loguru import logger

from src.price_monitor.data_quality.dq_dataclass import BusinessRulesReport
from src.price_monitor.utils.clock import today_dashed_str_with_key


def save_output_file_to_directory(config, data, file_name):
    data.to_csv(
        config["output"]["directory"]
        + "/"
        + today_dashed_str_with_key()
        + "/"
        + f"{file_name}.csv",
        index=False,
    )


def get_unique_identifier_column(data: pd.DataFrame) -> pd.DataFrame:
    required_columns = {"vehicle_id", "contract_type"}

    # Check for missing columns
    missing_columns = required_columns - set(data.columns)

    if missing_columns:
        # Raise an error and log it if required columns are missing
        error_message = f"Dataframe must contain columns: {', '.join(missing_columns)}"
        logger.error(error_message)
        raise ValueError(error_message)
    else:
        try:
            data["unique_car_line"] = data["vehicle_id"] + "_" + data["contract_type"]
            logger.debug(
                "Unique identifier using vehicle_id and contract_type created successfully."
            )
        except Exception as e:
            logger.warning(f"Failed to get unique car line column: {e}")

    return data


def filter_data(dataframe: pd.DataFrame, column1, column2):
    filtered_df = dataframe[(dataframe[column1] > 0) & (dataframe[column2] > 0)].dropna(
        subset=[column1, column2]
    )

    return filtered_df


def iterate_df_append_rules(
    input_data, rule_name, column_name, success_percentage, results, vendor, market
):
    total_rows = len(input_data)
    violations = total_rows * (100 - success_percentage) / 100
    result = BusinessRulesReport(
        vendor=vendor,
        market=market,
        rule_name=rule_name,
        column_name=column_name,
        success_percentage=success_percentage,
        violations=int(violations),
        total_rows=total_rows,
    )
    results.append(result)


def get_column_mapping():
    """
    Returns a dictionary that maps logical column names to actual column names in the DataFrame.
    Modify the values in this dictionary if the actual column names change in the DataFrame.
    """
    return {
        "monthly_rental_glp": "monthly_rental_glp",
        "monthly_rental_nlp": "monthly_rental_nlp",
        "total_payable_amount": "total_payable_amount",
        "otr": "otr",
        "total_deposit": "total_deposit",
        "deposit": "deposit",
        "vendor": "vendor",
        "market": "market",
        "unique_car_line": "unique_car_line",
        "total_credit_amount": "total_credit_amount",
        "optional_final_payment": "optional_final_payment",
        "fixed_roi": "fixed_roi",
        "apr": "apr",
        "series": "series",
        "currency": "currency",
        "option_purchase_fee": "option_purchase_fee",
        "add_on": "option_gross_list_price",
        "sales_offer": "sales_offer",
        "excess_milage": "excess_mileage",
        "annual_milage": "annual_mileage",
        "number_of_installments": "number_of_installments",
        "term_of_agreement": "term_of_agreement",
        "model_range_description": "model_range_description",
        "model_range_code": "model_range_code",
    }
