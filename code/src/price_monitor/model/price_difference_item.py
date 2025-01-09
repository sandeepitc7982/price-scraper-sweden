import dataclasses
from dataclasses import dataclass
from enum import StrEnum

from dataclasses_avroschema import AvroModel
from loguru import logger

from src.price_monitor.model.difference_item import DifferenceItem, DifferenceReason
from src.price_monitor.model.vendor import Currency, Market, Vendor
from src.price_monitor.utils.clock import current_timestamp_dashed_str_with_timezone


class PriceDifferenceReason(StrEnum):
    PRICE_INCREASE = "Price_Increase"
    PRICE_DECREASE = "Price_Decrease"
    NO_REASON = "No_Reason"
    OPTION_INCLUDED = "Option_Included"
    OPTION_EXCLUDED = "Option_Excluded"
    PRICE_INCREASE_OPTION_INCLUDED = "Price_Increase_Option_Included"
    PRICE_DECREASE_OPTION_INCLUDED = "Price_Decrease_Option_Included"
    PRICE_INCREASE_OPTION_EXCLUDED = "Price_Increase_Option_Excluded"
    PRICE_DECREASE_OPTION_EXCLUDED = "Price_Decrease_Option_Excluded"


@dataclass(eq=True)
class PriceDifferenceItem(AvroModel):
    recorded_at: str | None = dataclasses.field(default=None, compare=False)
    vendor: Vendor | None = dataclasses.field(default=None)
    series: str | None = dataclasses.field(default=None)
    model_range_code: str | None = dataclasses.field(default=None)
    model_range_description: str | None = dataclasses.field(default=None)
    model_code: str | None = dataclasses.field(default=None)
    model_description: str | None = dataclasses.field(default=None)
    line_code: str | None = dataclasses.field(default=None)
    line_description: str | None = dataclasses.field(default=None)
    market: Market | None = dataclasses.field(default=None)
    old_price: float | None = dataclasses.field(default=None)
    new_price: float | None = dataclasses.field(default=None)
    currency: str | None = dataclasses.field(default=None)
    perc_change: str | None = dataclasses.field(default=None)
    model_price_change: float | None = dataclasses.field(default=None)
    reason: PriceDifferenceReason | None = dataclasses.field(default=None)
    option_code: str | None = dataclasses.field(default=None)
    option_gross_list_price: float | None = dataclasses.field(default=None)
    option_net_list_price: float | None = dataclasses.field(default=None)


def _parse_price(value) -> float:
    try:
        price = float(value)
    except (ValueError, TypeError) as e:
        logger.error(f"Could not parse value: {value}, {e}")
        price = 0.0
    return price


def _create_price_difference_item_from_difference(
    difference_item: DifferenceItem,
) -> PriceDifferenceItem:
    option_code = ""
    option_gross_list_price = 0.0
    option_net_list_price = 0.0
    if difference_item.reason == DifferenceReason.PRICE_CHANGE:
        new_price = _parse_price(difference_item.new_value)
        old_price = _parse_price(difference_item.old_value)
    else:
        new_price = 0
        old_price = 0

    if difference_item.reason == DifferenceReason.OPTION_INCLUDED:
        reason = PriceDifferenceReason.OPTION_INCLUDED
        new_price, option_code = difference_item.new_value.split("/")
        (
            old_price,
            option_gross_list_price,
            option_net_list_price,
        ) = difference_item.old_value.split("/")
        new_price = _parse_price(new_price)
        old_price = _parse_price(old_price)
        option_gross_list_price = _parse_price(option_gross_list_price)
        option_net_list_price = _parse_price(option_net_list_price)
    elif difference_item.reason == DifferenceReason.OPTION_EXCLUDED:
        reason = PriceDifferenceReason.OPTION_EXCLUDED
        new_price, option_code = difference_item.new_value.split("/")
        old_price = _parse_price(difference_item.old_value)
        new_price = _parse_price(new_price)
    else:
        reason = (
            PriceDifferenceReason.PRICE_INCREASE
            if new_price > old_price
            else PriceDifferenceReason.PRICE_DECREASE
        )

    if old_price > 0:
        perc_change: float = abs(round((new_price - old_price) * 100 / old_price))
    else:
        perc_change = 0

    return PriceDifferenceItem(
        recorded_at=current_timestamp_dashed_str_with_timezone(),
        vendor=difference_item.vendor,
        series=difference_item.series,
        model_range_code=difference_item.model_range_code,
        model_range_description=difference_item.model_range_description,
        model_code=difference_item.model_code,
        model_description=difference_item.model_description,
        line_code=difference_item.line_code,
        line_description=difference_item.line_description,
        market=difference_item.market,
        old_price=old_price,
        new_price=new_price,
        currency=Currency[difference_item.market].value,
        perc_change=f"{perc_change}%",
        model_price_change=new_price - old_price,
        reason=reason,
        option_code=option_code,
        option_gross_list_price=option_gross_list_price,
        option_net_list_price=option_net_list_price,
    )
