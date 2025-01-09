# At the time of loading data as line items, we are extracting date from folder name
import dataclasses
from datetime import datetime, timezone
from typing import Type


def get_date_from_dir_name(target_dir) -> str:
    return target_dir.split("=")[-1]


def get_timestamp_from_dir_name(target_dir) -> str:
    date_str = target_dir.split("=")[-1]
    # Convert the date string to a datetime object
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    # Set the datetime object to UTC
    utc_date_obj = date_obj.replace(tzinfo=timezone.utc)

    # Format the datetime object to the desired string format
    return utc_date_obj.strftime("%Y-%m-%d %H:%M:%S %Z")


def get_csv_headers(model) -> list:
    headers = model.__annotations__.copy()
    return list(headers.keys())


def get_avro_schema(model) -> dict:
    avro_schema = model.avro_schema_to_python()
    return avro_schema


def filter_dataclass_attributes(record: dict, dataclass: Type[dataclasses]) -> dict:
    """
    Removes extra attributes present in data records
    but not defined as fields in our dataclass (ignores unknown attributes)
    """
    result: dict = dict()
    fields = [field.name for field in dataclasses.fields(dataclass)]

    for key in record.keys():
        if key in fields:
            result[key] = record[key]

    return result
