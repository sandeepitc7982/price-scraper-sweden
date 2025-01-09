import dataclasses
from dataclasses import dataclass
from typing import Optional

from dataclasses_avroschema import AvroModel
from strenum import StrEnum

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.utils.clock import current_timestamp_dashed_str_with_timezone


def build_difference_for_finance_item(
    finance_line_item: "FinanceLineItem",
    reason: "FinanceItemDifferenceReason",
    new_value: Optional[float] = None,
    old_value: Optional[float] = None,
) -> "DifferenceFinanceItem":
    return DifferenceFinanceItem(
        recorded_at=current_timestamp_dashed_str_with_timezone(),
        vehicle_id=finance_line_item.vehicle_id,
        vendor=finance_line_item.vendor,
        series=finance_line_item.series,
        model_range_code=finance_line_item.model_range_code,
        model_range_description=finance_line_item.model_range_description,
        model_code=finance_line_item.model_code,
        model_description=finance_line_item.model_description,
        line_code=finance_line_item.line_code,
        line_description=finance_line_item.line_description,
        contract_type=finance_line_item.contract_type,
        market=finance_line_item.market,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
    )


class FinanceItemDifferenceReason(StrEnum):
    PCP_NEW_LINE = "PCP_NEW_LINE"
    PCP_LINE_REMOVED = "PCP_LINE_REMOVED"
    PCP_MONTHLY_RENTAL_CHANGED = "PCP_MONTHLY_RENTAL_CHANGED"
    PCP_SALES_OFFER_CHANGED = "PCP_SALES_OFFER_CHANGED"
    PCP_OTR_CHANGED = "PCP_OTR_CHANGED"
    PCP_APR_CHANGED = "PCP_APR_CHANGED"
    PCP_FIXED_ROI_CHANGED = "PCP_FIXED_ROI_CHANGED"
    PCP_OPTIONAL_FINAL_PAYMENT_CHANGED = "PCP_OPTIONAL_FINAL_PAYMENT_CHANGED"


@dataclass
class DifferenceFinanceItem(AvroModel):
    recorded_at: str | None = dataclasses.field(default=None, compare=False)
    vehicle_id: str | None = dataclasses.field(default=None)
    vendor: Vendor | None = dataclasses.field(default=None)
    series: str | None = dataclasses.field(default=None)
    model_range_code: str | None = dataclasses.field(default=None)
    model_range_description: str | None = dataclasses.field(default=None)
    model_code: str | None = dataclasses.field(default=None)
    model_description: str | None = dataclasses.field(default=None)
    line_code: str | None = dataclasses.field(default=None)
    line_description: str | None = dataclasses.field(default=None)
    contract_type: str | None = dataclasses.field(default=None)
    market: Market | None = dataclasses.field(default=None)
    old_value: Optional[float] | None = dataclasses.field(default=None)
    new_value: Optional[float] | None = dataclasses.field(default=None)
    reason: FinanceItemDifferenceReason | None = dataclasses.field(default=None)
