import os
from fastavro import reader, writer
from loguru import logger

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.utils.clock import (
    today_dashed_str_with_key,
    yesterday_dashed_str_with_key,
)
from src.price_monitor.utils.csv_helper import (
    save_csv_for_line_item_repository,
    load_csv_for_line_item_repository,
)
from src.price_monitor.utils.io import get_avro_schema, filter_dataclass_attributes


class FileSystemLineItemRepository:
    def __init__(self, config: dict):  # sourcery skip: assign-if-exp
        output = config["output"]

        self.output_dir = output["directory"]
        self.filename = output["prices_filename"]
        if "file_type" in output:
            self.file_type = output["file_type"]
        else:
            self.file_type = "csv"
        self.yesterday_line_items: list[LineItem] = self.load(
            date=yesterday_dashed_str_with_key()
        )

    def save(self, line_items: list[LineItem], date: str = today_dashed_str_with_key()):
        target_dir = f"{self.output_dir}/{date}"
        os.makedirs(target_dir, exist_ok=True)
        logger.info(f"Saving file to {target_dir}/{self.filename}")
        if self.file_type == "avro":
            self._save_avro(target_dir=target_dir, line_items=line_items)
        # This is temporary until we migrate from csv to avro
        elif self.file_type == "dual":
            self._save_avro(target_dir=target_dir, line_items=line_items)
            save_csv_for_line_item_repository(
                filename=self.filename, target_dir=target_dir, line_items=line_items
            )
        else:
            save_csv_for_line_item_repository(
                filename=self.filename, target_dir=target_dir, line_items=line_items
            )
        if date == yesterday_dashed_str_with_key():
            self.yesterday_line_items = line_items

    def _save_avro(self, target_dir: str, line_items: list[LineItem]):
        with open(f"{target_dir}/{self.filename}.avro", "wb") as file:
            records: list[dict] = [line_item.asdict() for line_item in line_items]
            writer(file, get_avro_schema(LineItem), records, codec="deflate")

    def load(self, date: str) -> list[LineItem]:
        target_dir = f"{self.output_dir}/{date}"

        if self.file_type == "avro":
            response = self._load_avro(target_dir=target_dir)
            # If previous data was written in a different format
            if len(response) == 0:
                response = load_csv_for_line_item_repository(
                    filename=self.filename, target_dir=target_dir
                )
        else:
            response = load_csv_for_line_item_repository(
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

    def _load_avro(self, target_dir: str) -> list[LineItem]:
        response: list[LineItem] = []

        try:
            with open(f"{target_dir}/{self.filename}.avro", "rb") as file:
                avro_reader = reader(file)
                for record in avro_reader:
                    record["line_option_codes"] = [
                        LineItemOptionCode(**x) for x in record["line_option_codes"]
                    ]
                    response.append(
                        LineItem(
                            **filter_dataclass_attributes(record, dataclass=LineItem)
                        )
                    )
        except FileNotFoundError as e:
            logger.trace(f"No file found in {target_dir}", e)

        return response

    def load_market(self, date: str, market: Market, vendor: Vendor) -> list[LineItem]:
        if date == yesterday_dashed_str_with_key():
            full_price_list = self.yesterday_line_items
        else:
            full_price_list: list[LineItem] = self.load(date=date)
        return list(
            filter(
                lambda line_item: line_item.market == market
                and line_item.vendor == vendor,
                full_price_list,
            )
        )

    def load_model_filter_by_model_range_code(
        self, date: str, market: str, vendor: Vendor, series: str, model_range_code: str
    ) -> list[LineItem]:
        if date == yesterday_dashed_str_with_key():
            full_price_list = self.yesterday_line_items
        else:
            full_price_list: list[LineItem] = self.load(date=date)
        return list(
            filter(
                lambda line_item: line_item.market == market
                and line_item.vendor == vendor
                and line_item.series.lower() == series.lower()
                and line_item.model_range_code.lower() == model_range_code.lower(),
                full_price_list,
            )
        )

    def load_model_filter_by_model_range_description(
        self, date: str, market: str, vendor: Vendor, model_range_description: str
    ) -> list[LineItem]:
        if date == yesterday_dashed_str_with_key():
            full_price_list = self.yesterday_line_items
        else:
            full_price_list: list[LineItem] = self.load(date=date)
        return list(
            filter(
                lambda line_item: line_item.market == market
                and line_item.vendor == vendor
                and line_item.model_range_description.upper()
                == model_range_description.upper(),
                full_price_list,
            )
        )

    def load_model_filter_by_series(
        self, date: str, market: str, vendor: Vendor, series: str
    ) -> list[LineItem]:
        if date == yesterday_dashed_str_with_key():
            full_price_list = self.yesterday_line_items
        else:
            full_price_list: list[LineItem] = self.load(date=date)
        return list(
            filter(
                lambda line_item: line_item.market == market
                and line_item.vendor == vendor
                and line_item.series == series,
                full_price_list,
            )
        )

    def load_line_option_codes_for_line_code(
        self,
        date: str,
        market: str,
        vendor: Vendor,
        series: str,
        model_code: str,
        line_code: str,
    ) -> list[LineItemOptionCode]:
        line_item_for_trim_line = self.load_line_item_for_trim_line(
            date, market, vendor, series, model_code, line_code
        )
        if line_item_for_trim_line:
            return line_item_for_trim_line.line_option_codes
        return []

    def load_line_item_for_trim_line(
        self,
        date: str,
        market: str,
        vendor: Vendor,
        series: str,
        model_code: str,
        line_code: str,
    ) -> LineItem:
        if date == yesterday_dashed_str_with_key():
            full_price_list = self.yesterday_line_items
        else:
            full_price_list: list[LineItem] = self.load(date=date)
        line_item_for_trim_line = list(
            filter(
                lambda line_item: line_item.market == market
                and line_item.vendor == vendor
                and line_item.model_code == model_code
                and line_item.line_code == line_code
                and line_item.series == series,
                full_price_list,
            )
        )
        if len(line_item_for_trim_line) > 0:
            return line_item_for_trim_line[0]

    def load_model_filter_by_line_code(
        self, date: str, market: str, vendor: Vendor, line_code: str
    ) -> list[LineItem]:
        if date == yesterday_dashed_str_with_key():
            full_price_list = self.yesterday_line_items
        else:
            full_price_list: list[LineItem] = self.load(date=date)
        return list(
            filter(
                lambda line_item: line_item.market == market
                and line_item.vendor == vendor
                and line_item.line_code == line_code,
                full_price_list,
            )
        )

    def load_model_filter_by_model_code(
        self, date: str, market: str, vendor: Vendor, model_code: str
    ) -> list[LineItem]:
        if date == yesterday_dashed_str_with_key():
            full_price_list = self.yesterday_line_items
        else:
            full_price_list: list[LineItem] = self.load(date=date)
        return list(
            filter(
                lambda line_item: line_item.market == market
                and line_item.vendor == vendor
                and line_item.model_code == model_code,
                full_price_list,
            )
        )

    def load_model_filter_by_trim_line(
        self, date: str, market: str, vendor: Vendor, model_code: str, line_code: str
    ) -> list[LineItem]:
        if date == yesterday_dashed_str_with_key():
            full_price_list = self.yesterday_line_items
        else:
            full_price_list: list[LineItem] = self.load(date=date)
        return list(
            filter(
                lambda line_item: line_item.market == market
                and line_item.vendor == vendor
                and line_item.model_code == model_code
                and line_item.line_code == line_code,
                full_price_list,
            )
        )

    def update_line_items(
        self,
        existing_line_items: list[LineItem],
        new_line_items: list[LineItem],
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
