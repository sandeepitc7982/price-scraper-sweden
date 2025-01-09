import dataclasses
from dataclasses import dataclass
from typing import Optional

from dataclasses_avroschema import AvroModel
from strenum import StrEnum

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.utils.clock import current_timestamp_dashed_str_with_timezone


def build_difference_for(
    line_item: "LineItem",
    reason: "DifferenceReason",
    new_value: Optional[str] = None,
    old_value: Optional[str] = None,
) -> "DifferenceItem":
    return DifferenceItem(
        recorded_at=current_timestamp_dashed_str_with_timezone(),
        vendor=line_item.vendor,
        series=line_item.series,
        model_range_code=line_item.model_range_code,
        model_range_description=line_item.model_range_description,
        model_code=line_item.model_code,
        model_description=line_item.model_description,
        line_code=line_item.line_code,
        line_description=line_item.line_description,
        market=line_item.market,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
    )


class DifferenceReason(StrEnum):
    NEW_LINE = "NEW_LINE"
    LINE_REMOVED = "LINE_REMOVED"
    PRICE_CHANGE = "PRICE_CHANGE"
    OPTION_ADDED = "OPTION_ADDED"
    OPTION_REMOVED = "OPTION_REMOVED"
    OPTION_INCLUDED = "OPTION_INCLUDED"
    OPTION_EXCLUDED = "OPTION_EXCLUDED"
    OPTION_PRICE_CHANGE = "OPTION_PRICE_CHANGE"


@dataclass
class DifferenceItem(AvroModel):
    recorded_at: str | None = dataclasses.field(default=None, compare=False)
    vendor: Vendor | None = dataclasses.field(default=None)
    series: str | None = dataclasses.field(default=None)
    model_range_code: str | None = dataclasses.field(default=None)
    model_range_description: str | None = dataclasses.field(default=None)
    model_code: str | None = dataclasses.field(default=None)
    model_description: str | None = dataclasses.field(default=None)
    line_code: str | None = dataclasses.field(default=None)
    line_description: str | None = dataclasses.field(default=None)
    old_value: Optional[str] | None = dataclasses.field(default=None)
    new_value: Optional[str] | None = dataclasses.field(default=None)
    reason: DifferenceReason | None = dataclasses.field(default=None)
    market: Market | None = dataclasses.field(default=None)
