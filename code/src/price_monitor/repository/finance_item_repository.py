import os

from fastavro import reader, writer
from loguru import logger

from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.utils.clock import (
    today_dashed_str_with_key,
    yesterday_dashed_str_with_key,
)
from src.price_monitor.utils.csv_helper import (  # load_csv_for_line_item_repository,; save_csv_for_line_item_repository,
    load_csv_for_finance_line_item_repository,
    save_csv_for_finance_line_item_repository,
)
from src.price_monitor.utils.io import get_avro_schema, filter_dataclass_attributes


class FileSystemFinanceLineItemRepository:
    def __init__(self, config: dict):
        output = config["output"]

        self.output_dir = output["directory"]
        self.filename = output["finance_options_filename"]
        if "file_type" in output:
            self.file_type = output["file_type"]
        else:
            self.file_type = "csv"
        self.yesterday_finance_line_items: list[FinanceLineItem] = self.load(
            date=yesterday_dashed_str_with_key()
        )

    def save(
        self, line_items: list[FinanceLineItem], date: str = today_dashed_str_with_key()
    ):
        target_dir = f"{self.output_dir}/{date}"
        os.makedirs(target_dir, exist_ok=True)
        logger.info(f"Saving file to {target_dir}/{self.filename}")
        if self.file_type == "avro":
            self._save_avro(target_dir=target_dir, line_items=line_items)
        # This is temporary until we migrate from csv to avro
        elif self.file_type == "dual":
            self._save_avro(target_dir=target_dir, line_items=line_items)
            save_csv_for_finance_line_item_repository(
                filename=self.filename, target_dir=target_dir, line_items=line_items
            )
        else:
            save_csv_for_finance_line_item_repository(
                filename=self.filename, target_dir=target_dir, line_items=line_items
            )

    def _save_avro(self, target_dir: str, line_items: list[FinanceLineItem]):
        with open(f"{target_dir}/{self.filename}.avro", "wb") as file:
            records: list[dict] = [line_item.asdict() for line_item in line_items]
            for record in records:
                # While saving records to avro, for numerical fields need following assignments to have it read with default value
                record["term_of_agreement"] = int(record.get("term_of_agreement", 0))
            writer(file, get_avro_schema(FinanceLineItem), records, codec="deflate")

    def load(self, date: str) -> list[FinanceLineItem]:
        target_dir = f"{self.output_dir}/{date}"

        if self.file_type == "avro":
            response = self._load_avro(target_dir=target_dir)
            # If previous data was written in a different format
            if len(response) == 0:
                response = load_csv_for_finance_line_item_repository(
                    filename=self.filename, target_dir=target_dir
                )
        else:
            response = load_csv_for_finance_line_item_repository(
                filename=self.filename, target_dir=target_dir
            )
            # If previous data was written in a different format
            if len(response) == 0:
                response = self._load_avro(target_dir=target_dir)

        if len(response) == 0:
            logger.debug(
                f"No file found for date {date}. Trying to load from location {target_dir}, filename {self.filename}"
            )
        else:
            logger.info(f"Loaded {len(response)} items for date {date}")

        return response

    def _load_avro(self, target_dir: str) -> list[FinanceLineItem]:
        response: list[FinanceLineItem] = []

        try:
            with open(f"{target_dir}/{self.filename}.avro", "rb") as file:
                avro_reader = reader(file)
                for record in avro_reader:
                    response.append(
                        FinanceLineItem(
                            **filter_dataclass_attributes(
                                record, dataclass=FinanceLineItem
                            )
                        )
                    )
        except FileNotFoundError as e:
            logger.trace(f"No file found in {target_dir}", e)

        return response

    def update_finance_line_item(
        self,
        existing_line_items: list[FinanceLineItem],
        new_line_items: list[FinanceLineItem],
        config: dict,
    ):
        combos = [
            (vendor, market)
            for vendor, markets in config["scraper"]["enabled"].items()
            for market in markets
        ]
        previously_scraper_line_items = list(
            filter(lambda x: (x.vendor, x.market) not in combos, existing_line_items)
        )
        updated_line_items = previously_scraper_line_items + new_line_items
        self.save(updated_line_items)

    def load_market(
        self, date: str, market: Market, vendor: Vendor
    ) -> list[FinanceLineItem]:
        if date == yesterday_dashed_str_with_key():
            full_finance_list = self.yesterday_finance_line_items
        else:
            full_finance_list: list[FinanceLineItem] = self.load(date=date)
        return list(
            filter(
                lambda finance_line_item: finance_line_item.market == market
                and finance_line_item.vendor == vendor,
                full_finance_list,
            )
        )

    def load_model_filter_by_model_range_description(
        self, date: str, market: str, vendor: Vendor, model_range_description: str
    ) -> list[FinanceLineItem]:
        if date == yesterday_dashed_str_with_key():
            full_finance_list = self.yesterday_finance_line_items
        else:
            full_finance_list: list[FinanceLineItem] = self.load(date=date)
        return list(
            filter(
                lambda finance_line_item: finance_line_item.market == market
                and finance_line_item.vendor == vendor
                and finance_line_item.model_range_description.upper()
                == model_range_description.upper(),
                full_finance_list,
            )
        )

    def load_model_filter_by_line_code(
        self,
        date: str,
        market: str,
        vendor: Vendor,
        series: str,
        model_range_code: str,
        model_code: str,
        line_code: str,
    ) -> list[FinanceLineItem]:
        if date == yesterday_dashed_str_with_key():
            full_finance_list = self.yesterday_finance_line_items
        else:
            full_finance_list: list[FinanceLineItem] = self.load(date=date)
        return list(
            filter(
                lambda finance_line_item: finance_line_item.market == market
                and finance_line_item.vendor == vendor
                and finance_line_item.model_range_code.lower()
                == model_range_code.lower()
                and finance_line_item.model_code.lower() == model_code.lower()
                and finance_line_item.line_code.lower() == line_code.lower()
                and finance_line_item.series.lower() == series.lower(),
                full_finance_list,
            )
        )

    def load_model_filter_by_series(
        self, date: str, market: str, vendor: Vendor, series: str
    ) -> list[FinanceLineItem]:
        if date == yesterday_dashed_str_with_key():
            full_finance_list = self.yesterday_finance_line_items
        else:
            full_finance_list: list[FinanceLineItem] = self.load(date=date)
        return list(
            filter(
                lambda finance_line_item: finance_line_item.market == market
                and finance_line_item.vendor == vendor
                and finance_line_item.series.upper() == series.upper(),
                full_finance_list,
            )
        )
