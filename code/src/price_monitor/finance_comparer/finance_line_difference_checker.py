from loguru import logger

from src.price_monitor.finance_comparer.difference_finance_item import (
    FinanceItemDifferenceReason,
    DifferenceFinanceItem,
    build_difference_for_finance_item,
)
from src.price_monitor.model.finance_line_item import FinanceLineItem


def _check_differences_between_existing_pcp_items(
    current: list[FinanceLineItem], previous: list[FinanceLineItem]
) -> list[DifferenceFinanceItem]:

    differences_between_items: list[DifferenceFinanceItem] = []
    removed_items: list[DifferenceFinanceItem] = []

    for previous_item in previous:
        if previous_item not in current:
            removed_items.append(
                build_difference_for_finance_item(
                    finance_line_item=previous_item,
                    reason=FinanceItemDifferenceReason.PCP_LINE_REMOVED,
                )
            )

        for current_item in current:
            if current_item == previous_item:
                difference = current_item.pcp_difference_with(other=previous_item)
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


def _check_for_new_pcp_items(
    current: list[FinanceLineItem], previous: list[FinanceLineItem]
) -> tuple[list[DifferenceFinanceItem], list[FinanceLineItem]]:

    new_items: list[DifferenceFinanceItem] = []
    remaining_current_items: list[FinanceLineItem] = []

    for current_item in current:
        if current_item not in previous:
            new_items.append(
                build_difference_for_finance_item(
                    finance_line_item=current_item,
                    reason=FinanceItemDifferenceReason.PCP_NEW_LINE,
                )
            )
        else:
            remaining_current_items.append(current_item)

    logger.info(
        f"Found {len(new_items)} new item(s) between current and previous datasets"
    )

    return new_items, remaining_current_items


def check_item_differences(
    current: list[FinanceLineItem], previous: list[FinanceLineItem]
) -> list[DifferenceFinanceItem]:

    item_differences: list[DifferenceFinanceItem] = []

    current_pcp_data = [
        pcp_current_items
        for pcp_current_items in current
        if pcp_current_items.contract_type == "PCP"
    ]

    previous_pcp_data = [
        pcp_previous_items
        for pcp_previous_items in previous
        if pcp_previous_items.contract_type == "PCP"
    ]

    (new_items, remaining_current_items) = _check_for_new_pcp_items(
        current=current_pcp_data, previous=previous_pcp_data
    )

    existing_differences: list[DifferenceFinanceItem] = (
        _check_differences_between_existing_pcp_items(
            current=remaining_current_items, previous=previous_pcp_data
        )
    )

    item_differences.extend(existing_differences)
    item_differences.extend(new_items)

    return item_differences
