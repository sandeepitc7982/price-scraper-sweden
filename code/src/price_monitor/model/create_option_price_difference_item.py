import json

from loguru import logger

from src.price_monitor.model.difference_item import DifferenceItem, DifferenceReason
from src.price_monitor.model.option_price_difference_item import (
    OptionPriceDifferenceItem,
    OptionPriceDifferenceReason,
    build_option_price_difference_item,
)
from src.price_monitor.model.price_difference_item import _parse_price
from src.price_monitor.model.vendor import Currency
from src.price_monitor.utils.clock import current_timestamp_dashed_str_with_timezone


def create_option_price_difference_item(
    differences: list[DifferenceItem],
) -> list[OptionPriceDifferenceItem]:
    option_price_differences: list[OptionPriceDifferenceItem] = []
    option_price_difference_list = list(
        filter(
            lambda diff_item: diff_item.reason == DifferenceReason.OPTION_PRICE_CHANGE,
            differences,
        ),
    )

    line_item_group = {}
    for option in option_price_difference_list:
        key = option.market + option.vendor + option.old_value + option.new_value
        line_item_group[key] = line_item_group.get(key, [])
        line_item_group[key].append(option)

    for group, list_of_grouped_line_item in line_item_group.items():
        if len(list_of_grouped_line_item) > 0:
            option_price_diff = (
                create_option_price_difference_item_with_merged_model_range(
                    list_of_grouped_line_item
                )
            )
            if option_price_diff:
                option_price_differences.append(option_price_diff)

    return option_price_differences


def _create_option_price_difference_item_from_difference(
    difference_items: list[DifferenceItem], model_range: str
) -> OptionPriceDifferenceItem:
    perc_change: float = 0.00
    try:
        if len(difference_items) == 0:
            raise Exception("Empty differences")
        difference_item = difference_items[0]
        old_value_dictionary = json.loads(difference_item.old_value)
        option_description = old_value_dictionary["option_description"]
        option_old_price = _parse_price(old_value_dictionary["old_price"])
        option_new_price = _parse_price(difference_item.new_value)

        if option_old_price == option_new_price:
            raise Exception(
                f"Equal old price and new price for option {difference_item}"
            )

        reason = (
            OptionPriceDifferenceReason.PRICE_INCREASE
            if option_new_price > option_old_price
            else OptionPriceDifferenceReason.PRICE_DECREASE
        )
        if option_old_price > 0:
            perc_change: float = round(
                (option_new_price - option_old_price) * 100 / option_old_price
            )

        return build_option_price_difference_item(
            recorded_at=current_timestamp_dashed_str_with_timezone(),
            vendor=difference_item.vendor,
            market=difference_item.market,
            option_description=option_description,
            option_old_price=option_old_price,
            option_new_price=option_new_price,
            currency=Currency[difference_item.market].value,
            perc_change=f"{perc_change}%",
            option_price_change=option_new_price - option_old_price,
            reason=reason,
            model_range_description=model_range,
        )
    except Exception as e:
        logger.exception(f"Error loading json from {difference_items}, exception: {e}")


def create_option_price_difference_item_with_merged_model_range(
    differences: list[DifferenceItem],
) -> OptionPriceDifferenceItem:
    model_range = set()
    for difference in differences:
        model_range.add(difference.model_range_description)
    model_range = sorted(model_range, reverse=False)
    model_range = ", ".join(model_range)

    return _create_option_price_difference_item_from_difference(
        differences, model_range
    )
