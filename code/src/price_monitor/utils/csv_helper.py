import ast
import csv
import dataclasses
import json

from loguru import logger

from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.utils.io import (
    get_csv_headers,
    filter_dataclass_attributes,
    get_timestamp_from_dir_name,
)


def save_csv_for_line_item_repository(
    filename: str, target_dir: str, line_items: list[LineItem]
):
    with open(f"{target_dir}/{filename}.csv", "w", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=get_csv_headers(LineItem))
        writer.writeheader()
        rows = [dataclasses.asdict(x) for x in line_items]
        for row in rows:
            row["line_option_codes"] = json.dumps(row["line_option_codes"])
        writer.writerows(rows)


def save_csv_for_finance_line_item_repository(
    filename: str, target_dir: str, line_items: list[FinanceLineItem]
):
    with open(f"{target_dir}/{filename}.csv", "w", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=get_csv_headers(FinanceLineItem))
        writer.writeheader()
        rows = [dataclasses.asdict(x) for x in line_items]
        writer.writerows(rows)


def load_csv_for_line_item_repository(filename: str, target_dir: str) -> list[LineItem]:
    response: list[LineItem] = []
    try:
        with open(f"{target_dir}/{filename}.csv", "r", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                options = json.loads(row["line_option_codes"])
                row["line_option_codes"] = json.dumps(options)

                row["line_option_codes"] = [
                    LineItemOptionCode(**x)
                    for x in ast.literal_eval(str(json.loads(row["line_option_codes"])))
                ]
                row["net_list_price"] = float(row["net_list_price"])
                row["gross_list_price"] = float(row["gross_list_price"])
                row["recorded_at"] = get_timestamp_from_dir_name(target_dir)

                response.append(
                    LineItem(**filter_dataclass_attributes(row, dataclass=LineItem))
                )
    except FileNotFoundError as e:
        logger.trace(f"No file found in {target_dir}", e)

    return response


def load_csv_for_finance_line_item_repository(
    filename: str, target_dir: str
) -> list[FinanceLineItem]:
    response: list[FinanceLineItem] = []
    try:
        with open(f"{target_dir}/{filename}.csv", "r", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                row["monthly_rental_nlp"] = float(row["monthly_rental_nlp"])
                row["monthly_rental_glp"] = float(row["monthly_rental_glp"])
                # Data read from a CSV file is always in text format, and for new numerical fields need following assignments to have it read with default value.
                if "number_of_installments" not in row:
                    row["number_of_installments"] = 0
                else:
                    row["number_of_installments"] = int(row["number_of_installments"])
                response.append(
                    FinanceLineItem(
                        **filter_dataclass_attributes(row, dataclass=FinanceLineItem)
                    )
                )
    except FileNotFoundError as e:
        logger.trace(f"No file found in {target_dir}", e)

    return response


def save_csv_for_difference_item_saver(
    target_dir: str, filename: str, difference_items: list, item_schema
):
    with open(f"{target_dir}/{filename}.csv", "w", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=get_csv_headers(item_schema))
        writer.writeheader()
        rows = [dataclasses.asdict(x) for x in difference_items]
        writer.writerows(rows)


def load_csv_for_difference_item_loader(
    differences_filename: str, target_dir: str, difference_item_class
) -> list:
    response: list[difference_item_class] = []
    with open(
        f"{target_dir}/{differences_filename}.csv", "r", encoding="utf-8"
    ) as file:
        for row in csv.DictReader(file):
            row["recorded_at"] = get_timestamp_from_dir_name(target_dir)
            response.append(difference_item_class(**row))
    if not response:
        logger.warning(
            f"No data changes found in file {target_dir}/{differences_filename}.csv"
        )

    return response


def load_csv_for_difference_finance_item_loader(
    differences_filename: str, target_dir: str, difference_item_class
) -> list:
    response: list[difference_item_class] = []
    with open(
        f"{target_dir}/{differences_filename}.csv", "r", encoding="utf-8"
    ) as file:
        for row in csv.DictReader(file):
            row["recorded_at"] = get_timestamp_from_dir_name(target_dir)
            row["old_value"] = float(row["old_value"])
            row["new_value"] = float(row["new_value"])
            response.append(difference_item_class(**row))
    if not response:
        logger.warning(
            f"No data changes found in file {target_dir}/{differences_filename}.csv"
        )

    return response
