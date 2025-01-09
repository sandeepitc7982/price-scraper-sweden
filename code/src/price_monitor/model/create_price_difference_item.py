import itertools

from src.price_monitor.model.difference_item import DifferenceItem, DifferenceReason
from src.price_monitor.model.price_difference_item import (
    PriceDifferenceItem,
    PriceDifferenceReason,
    _create_price_difference_item_from_difference,
)


def create_price_difference_item(
    differences: list[DifferenceItem],
) -> list[PriceDifferenceItem]:
    price_differences: list[PriceDifferenceItem] = []
    price_difference_list = list(
        filter(
            lambda diff_item: diff_item.reason == DifferenceReason.PRICE_CHANGE
            or diff_item.reason == DifferenceReason.OPTION_INCLUDED
            or diff_item.reason == DifferenceReason.OPTION_EXCLUDED,
            differences,
        ),
    )

    line_item_group = itertools.groupby(
        price_difference_list,
        key=(
            lambda price_difference: (
                price_difference.series,
                price_difference.model_range_code,
                price_difference.model_range_description,
                price_difference.model_code,
                price_difference.model_description,
                price_difference.line_code,
                price_difference.line_description,
            )
        ),
    )

    for group, list_of_grouped_line_item in line_item_group:
        price_differences.extend(
            create_price_difference_item_with_merged_reason(
                list(list_of_grouped_line_item)
            )
        )

    return price_differences


def create_price_difference_item_with_merged_reason(
    list_of_difference_item: list[DifferenceItem],
) -> list[PriceDifferenceItem]:
    if len(list_of_difference_item) == 1:
        return [
            _create_price_difference_item_from_difference(list_of_difference_item[0])
        ]

    list_of_price_difference = list(
        map(_create_price_difference_item_from_difference, list_of_difference_item)
    )
    list_of_reasons = set(
        [price_difference.reason for price_difference in list_of_price_difference]
    )

    list_of_option_included = _filter_by_reason(
        list_of_price_difference, PriceDifferenceReason.OPTION_INCLUDED
    )
    list_of_option_excluded = _filter_by_reason(
        list_of_price_difference, PriceDifferenceReason.OPTION_EXCLUDED
    )

    if sorted(list_of_reasons) == [
        PriceDifferenceReason.OPTION_EXCLUDED,
        PriceDifferenceReason.OPTION_INCLUDED,
    ]:
        return list_of_price_difference

    map_list_of_reasons_to_merged_reason = _create_map_reasons(
        list_of_option_included, list_of_option_excluded
    )

    for (
        reasons_list_map,
        list_to_change,
        merged_reason,
    ) in map_list_of_reasons_to_merged_reason:
        if set(reasons_list_map).issubset(list_of_reasons):
            _set_reason_to_price_diff(list_to_change, merged_reason)

    price_differences: list[PriceDifferenceItem] = []
    price_differences.extend(list_of_option_included)
    price_differences.extend(list_of_option_excluded)

    return _filter_only_combined_reasons(price_differences)


def _create_map_reasons(
    list_of_option_included: list[PriceDifferenceItem],
    list_of_option_excluded: list[PriceDifferenceItem],
) -> list[
    (list[PriceDifferenceReason], list[PriceDifferenceItem], PriceDifferenceReason)
]:
    price_increase_option_included = [
        PriceDifferenceReason.OPTION_INCLUDED,
        PriceDifferenceReason.PRICE_INCREASE,
    ]
    price_increase_option_excluded = [
        PriceDifferenceReason.OPTION_EXCLUDED,
        PriceDifferenceReason.PRICE_INCREASE,
    ]
    price_decrease_option_included = [
        PriceDifferenceReason.OPTION_INCLUDED,
        PriceDifferenceReason.PRICE_DECREASE,
    ]
    price_decrease_option_excluded = [
        PriceDifferenceReason.OPTION_EXCLUDED,
        PriceDifferenceReason.PRICE_DECREASE,
    ]

    return [
        (
            price_increase_option_included,
            list_of_option_included,
            PriceDifferenceReason.PRICE_INCREASE_OPTION_INCLUDED,
        ),
        (
            price_decrease_option_excluded,
            list_of_option_excluded,
            PriceDifferenceReason.PRICE_DECREASE_OPTION_EXCLUDED,
        ),
        (
            price_increase_option_excluded,
            list_of_option_excluded,
            PriceDifferenceReason.PRICE_INCREASE_OPTION_EXCLUDED,
        ),
        (
            price_decrease_option_included,
            list_of_option_included,
            PriceDifferenceReason.PRICE_DECREASE_OPTION_INCLUDED,
        ),
    ]


def _set_reason_to_price_diff(
    price_differences: list[PriceDifferenceItem], reason: PriceDifferenceReason
):
    for price_difference in price_differences:
        price_difference.reason = reason


def _filter_only_combined_reasons(list_of_price_difference: list[PriceDifferenceItem]):
    return list(
        filter(
            lambda price_difference: price_difference.reason
            in [
                PriceDifferenceReason.PRICE_INCREASE_OPTION_INCLUDED,
                PriceDifferenceReason.PRICE_DECREASE_OPTION_EXCLUDED,
                PriceDifferenceReason.PRICE_INCREASE_OPTION_EXCLUDED,
                PriceDifferenceReason.PRICE_DECREASE_OPTION_INCLUDED,
            ],
            list_of_price_difference,
        )
    )


def _filter_by_reason(
    list_of_price_difference: list[PriceDifferenceItem], reason: PriceDifferenceReason
) -> list[PriceDifferenceItem]:
    return list(
        filter(
            lambda price_difference_alias: price_difference_alias.reason == reason,
            list_of_price_difference,
        )
    )
