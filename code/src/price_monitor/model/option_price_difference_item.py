import dataclasses
from dataclasses import dataclass

from dataclasses_avroschema import AvroModel
from strenum import StrEnum

from src.price_monitor.model.vendor import Market, Vendor


class OptionPriceDifferenceReason(StrEnum):
    PRICE_INCREASE = "PRICE_INCREASE"
    PRICE_DECREASE = "PRICE_DECREASE"


@dataclass
class OptionPriceDifferenceItem(AvroModel):
    recorded_at: str | None = dataclasses.field(default=None, compare=False)
    vendor: Vendor | None = dataclasses.field(default=None)
    market: Market | None = dataclasses.field(default=None)
    option_description: str | None = dataclasses.field(default=None)
    option_old_price: float | None = dataclasses.field(default=None)
    option_new_price: float | None = dataclasses.field(default=None)
    currency: str | None = dataclasses.field(default=None)
    perc_change: str | None = dataclasses.field(default=None)
    option_price_change: float | None = dataclasses.field(default=None)
    reason: OptionPriceDifferenceReason | None = dataclasses.field(default=None)
    model_range_description: str | None = dataclasses.field(default=None)


def build_option_price_difference_item(
    recorded_at: str,
    vendor: Vendor,
    market: Market,
    option_description: str,
    option_old_price: float,
    option_new_price: float,
    currency: str,
    perc_change: str,
    option_price_change: float,
    reason: OptionPriceDifferenceReason,
    model_range_description: str,
) -> OptionPriceDifferenceItem:
    return OptionPriceDifferenceItem(
        recorded_at=recorded_at,
        vendor=vendor,
        market=market,
        option_description=option_description,
        option_old_price=option_old_price,
        option_new_price=option_new_price,
        currency=currency,
        perc_change=perc_change,
        option_price_change=option_price_change,
        reason=reason,
        model_range_description=model_range_description,
    )
