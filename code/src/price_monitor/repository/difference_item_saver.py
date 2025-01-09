import os

from fastavro import writer

from src.price_monitor.model.difference_item import DifferenceItem, DifferenceReason
from src.price_monitor.model.option_price_difference_item import (
    OptionPriceDifferenceItem,
)
from src.price_monitor.model.price_difference_item import PriceDifferenceItem
from src.price_monitor.utils.clock import today_dashed_str_with_key
from src.price_monitor.utils.csv_helper import save_csv_for_difference_item_saver
from src.price_monitor.utils.io import get_avro_schema


class DifferenceItemSaver:
    def __init__(self, output_dir, file_type, differences_filename):
        self.differences_filename = differences_filename
        self.file_type = file_type
        self.output_dir = output_dir
        self.target_dir = f"{self.output_dir}/{today_dashed_str_with_key()}"
        os.makedirs(self.target_dir, exist_ok=True)

    def save_differences(self, difference_items):
        diff_schema = DifferenceItem
        difference_items = list(
            filter(
                lambda x: x.reason != DifferenceReason.OPTION_INCLUDED
                and x.reason != DifferenceReason.OPTION_EXCLUDED
                and x.reason != DifferenceReason.OPTION_PRICE_CHANGE,
                difference_items,
            )
        )
        diffs_to_save = self.differences_filename
        self.save(diff_schema, difference_items, diffs_to_save)

    def save_price_differences(self, difference_items):
        diffs_to_save = "price_changelog"
        diff_schema = PriceDifferenceItem
        self.save(diff_schema, difference_items, diffs_to_save)

    def save_option_price_differences(self, difference_items):
        diffs_to_save = "option_price_changelog"
        diff_schema = OptionPriceDifferenceItem
        self.save(diff_schema, difference_items, diffs_to_save)

    def save(
        self,
        diff_schema,
        difference_items: list,
        diffs_to_save: str,
    ):
        if self.file_type == "avro":
            self._save_avro(
                filename=diffs_to_save,
                difference_items=difference_items,
                item_schema=diff_schema,
            )
        # This is temporary until we migrate from csv to avro
        elif self.file_type == "dual":
            self._save_avro(
                filename=diffs_to_save,
                difference_items=difference_items,
                item_schema=diff_schema,
            )
            save_csv_for_difference_item_saver(
                target_dir=self.target_dir,
                filename=diffs_to_save,
                difference_items=difference_items,
                item_schema=diff_schema,
            )
        else:
            save_csv_for_difference_item_saver(
                target_dir=self.target_dir,
                filename=diffs_to_save,
                difference_items=difference_items,
                item_schema=diff_schema,
            )

    def _save_avro(self, filename: str, difference_items: list, item_schema):
        with open(f"{self.target_dir}/{filename}.avro", "wb") as file:
            records: list[dict] = [
                difference_item.asdict() for difference_item in difference_items
            ]
            writer(file, get_avro_schema(item_schema), records, codec="deflate")
