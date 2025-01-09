from src.price_monitor.finance_comparer.difference_finance_item import (
    DifferenceFinanceItem,
)
from src.price_monitor.finance_comparer.finance_line_difference_checker import (
    check_item_differences,
)
from src.price_monitor.finance_comparer.difference_finance_item_repository import (
    DifferenceFinanceItemRepository,
)
from src.price_monitor.repository.finance_item_repository import (
    FileSystemFinanceLineItemRepository,
)
from src.price_monitor.utils.clock import (
    today_dashed_str_with_key,
    yesterday_dashed_str_with_key,
)


class FinanceOptionsComparator:
    def __init__(self, config) -> None:
        self.differences_finance_item_repository = DifferenceFinanceItemRepository(
            config=config
        )
        self.finance_item_repository = FileSystemFinanceLineItemRepository(
            config=config
        )

    def compare(self):

        differences = self._load_differences()

        self.differences_finance_item_repository.save(
            differences, DifferenceFinanceItem
        )

    def _load_differences(self) -> list[DifferenceFinanceItem]:
        prev_day_line_items = self.finance_item_repository.load(
            date=yesterday_dashed_str_with_key()
        )
        today_line_items = self.finance_item_repository.load(
            date=today_dashed_str_with_key()
        )

        return check_item_differences(
            current=today_line_items, previous=prev_day_line_items
        )
