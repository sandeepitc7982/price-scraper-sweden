from loguru import logger

from src.price_monitor.model.create_option_price_difference_item import (
    create_option_price_difference_item,
)
from src.price_monitor.model.create_price_difference_item import (
    create_price_difference_item,
)
from src.price_monitor.model.difference_item import (
    DifferenceItem,
    DifferenceReason,
    build_difference_for,
)
from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.option_price_difference_item import (
    OptionPriceDifferenceItem,
)
from src.price_monitor.model.price_difference_item import PriceDifferenceItem


def _check_differences_between_existing_items(
    current: list[LineItem], previous: list[LineItem]
) -> list[DifferenceItem]:
    differences_between_items: list[DifferenceItem] = []
    removed_items: list[DifferenceItem] = []

    for previous_item in previous:
        if previous_item not in current:
            removed_items.append(
                build_difference_for(
                    line_item=previous_item, reason=DifferenceReason.LINE_REMOVED
                )
            )

        for current_item in current:
            if current_item == previous_item:
                difference = current_item.difference_with(other=previous_item)
                differences_between_items.extend(difference)
                break

    logger.info(
        f"Found {len(differences_between_items)} difference(s) between existing items in current and previous "
        f"datasets"
    )
    logger.info(
        f"Found {len(removed_items)} removed item(s) between current and previous datasets"
    )

    differences_between_items.extend(removed_items)
    return differences_between_items


def _check_for_new_items(
    current: list[LineItem], previous: list[LineItem]
) -> tuple[list[DifferenceItem], list[LineItem]]:
    new_items: list[DifferenceItem] = []
    remaining_current_items: list[LineItem] = []

    for current_item in current:
        if current_item not in previous:
            new_items.append(
                build_difference_for(
                    line_item=current_item, reason=DifferenceReason.NEW_LINE
                )
            )
        else:
            remaining_current_items.append(current_item)

    logger.info(
        f"Found {len(new_items)} new item(s) between current and previous datasets"
    )

    return new_items, remaining_current_items


def check_item_differences(
    current: list[LineItem], previous: list[LineItem]
) -> tuple[
    list[DifferenceItem], list[PriceDifferenceItem], list[OptionPriceDifferenceItem]
]:
    item_differences: list[DifferenceItem] = []

    (new_items, remaining_current_items) = _check_for_new_items(
        current=current, previous=previous
    )

    existing_differences: list[DifferenceItem] = (
        _check_differences_between_existing_items(
            current=remaining_current_items, previous=previous
        )
    )

    item_differences.extend(existing_differences)
    item_differences.extend(new_items)

    price_differences = create_price_difference_item(item_differences)

    option_price_differences = create_option_price_difference_item(item_differences)

    return item_differences, price_differences, option_price_differences
