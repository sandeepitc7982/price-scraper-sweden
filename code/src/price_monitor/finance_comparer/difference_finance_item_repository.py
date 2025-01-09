import os

from loguru import logger

from src.price_monitor.finance_comparer.difference_finance_item import (
    DifferenceFinanceItem,
)
from src.price_monitor.finance_comparer.difference_finance_item_loader import (
    DifferenceFinanceItemLoader,
)
from src.price_monitor.finance_comparer.difference_finance_item_saver import (
    DifferenceFinanceItemSaver,
)
from src.price_monitor.utils.clock import today_dashed_str_with_key


class DifferenceFinanceItemRepository:
    def __init__(self, config: dict):
        output = config["output"]

        self.differences_filename = (
            f"{output['finance_options_filename']}_{output['differences_filename']}"
        )
        self.file_type = output["file_type"] if "file_type" in output else "csv"
        self.output_dir = output["directory"]
        self.target_dir = f"{self.output_dir}/{today_dashed_str_with_key()}"
        os.makedirs(self.target_dir, exist_ok=True)

        self.loader = DifferenceFinanceItemLoader(
            self.output_dir, self.file_type, self.differences_filename
        )
        self.saver = DifferenceFinanceItemSaver(
            self.output_dir, self.file_type, self.differences_filename
        )

    def save(self, difference_items: list, difference_item_instance):
        if difference_item_instance == DifferenceFinanceItem:
            self.saver.save_differences(difference_items=difference_items)

    def load(self, date: str, difference_item_class) -> list:
        try:
            return self.loader.load(date, difference_item_class)
        except FileNotFoundError as e:
            logger.error(f"File was not found for date {date}, {e}")
            return []
