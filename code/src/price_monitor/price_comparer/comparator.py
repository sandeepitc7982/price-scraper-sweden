from src.price_monitor.model.difference_item import DifferenceItem
from src.price_monitor.model.option_price_difference_item import (
    OptionPriceDifferenceItem,
)
from src.price_monitor.model.price_difference_item import PriceDifferenceItem
from src.price_monitor.price_comparer.line_diff_checker import check_item_differences
from src.price_monitor.repository.difference_item_repository import (
    DifferenceItemRepository,
)
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.utils.clock import (
    today_dashed_str_with_key,
    yesterday_dashed_str_with_key,
)


class Comparator:
    def __init__(self, config) -> None:
        self.differences_repository = DifferenceItemRepository(config=config)
        self.line_item_repository = FileSystemLineItemRepository(config=config)

    def compare(self):
        (
            differences,
            price_differences,
            option_price_differences,
        ) = self._load_differences()
        self.differences_repository.save(differences, DifferenceItem)
        self.differences_repository.save(price_differences, PriceDifferenceItem)
        self.differences_repository.save(
            option_price_differences, OptionPriceDifferenceItem
        )

    def _load_differences(
        self,
    ) -> tuple[
        list[DifferenceItem], list[PriceDifferenceItem], list[OptionPriceDifferenceItem]
    ]:
        prev_day_line_items = self.line_item_repository.load(
            date=yesterday_dashed_str_with_key()
        )
        today_line_items = self.line_item_repository.load(
            date=today_dashed_str_with_key()
        )

        return check_item_differences(
            current=today_line_items, previous=prev_day_line_items
        )
