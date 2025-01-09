import os

from loguru import logger

from src.price_monitor.model.difference_item import DifferenceItem
from src.price_monitor.model.option_price_difference_item import (
    OptionPriceDifferenceItem,
)
from src.price_monitor.model.price_difference_item import PriceDifferenceItem
from src.price_monitor.repository.difference_item_loader import DifferenceItemLoader
from src.price_monitor.repository.difference_item_saver import DifferenceItemSaver
from src.price_monitor.utils.clock import today_dashed_str_with_key


class DifferenceItemRepository:
    def __init__(self, config: dict):
        output = config["output"]

        self.differences_filename = output["differences_filename"]
        self.file_type = output["file_type"] if "file_type" in output else "csv"
        self.output_dir = output["directory"]
        self.target_dir = f"{self.output_dir}/{today_dashed_str_with_key()}"
        os.makedirs(self.target_dir, exist_ok=True)

        self.loader = DifferenceItemLoader(
            self.output_dir, self.file_type, self.differences_filename
        )
        self.saver = DifferenceItemSaver(
            self.output_dir, self.file_type, self.differences_filename
        )

    def save(self, difference_items: list, difference_item_instance):
        if difference_item_instance == DifferenceItem:
            self.saver.save_differences(difference_items=difference_items)
        elif difference_item_instance == PriceDifferenceItem:
            self.saver.save_price_differences(difference_items=difference_items)
        elif difference_item_instance == OptionPriceDifferenceItem:
            self.saver.save_option_price_differences(difference_items=difference_items)

    def load(self, date: str, difference_item_class) -> list:
        try:
            return self.loader.load(date, difference_item_class)
        except FileNotFoundError as e:
            logger.error(f"File was not found for date {date}, {e}")
            return []
