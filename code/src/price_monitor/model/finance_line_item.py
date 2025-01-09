import dataclasses
import hashlib
from dataclasses import dataclass

from dataclasses_avroschema import AvroModel

from src.price_monitor.finance_comparer.difference_finance_item import (
    DifferenceFinanceItem,
    build_difference_for_finance_item,
    FinanceItemDifferenceReason,
)
from src.price_monitor.model.vendor import Currency, Market, Vendor
from src.price_monitor.utils.clock import (
    today_dashed_str,
    current_timestamp_dashed_str_with_timezone,
)
from src.price_monitor.utils.utils import validate_not_blank_or_empty


@dataclass(eq=True)
class FinanceLineItem(AvroModel):
    recorded_at: str | None = dataclasses.field(default=None, compare=False)
    vehicle_id: str | None = dataclasses.field(default=None, compare=True)
    market: Market | None = dataclasses.field(default=None, compare=False)
    currency: str | None = dataclasses.field(default=None, compare=False)
    vendor: Vendor | None = dataclasses.field(default=None, compare=False)
    series: str | None = dataclasses.field(default=None, compare=False)
    model_range_code: str | None = dataclasses.field(default=None, compare=False)
    model_range_description: str | None = dataclasses.field(default=None, compare=False)
    model_code: str | None = dataclasses.field(default=None, compare=False)
    model_description: str | None = dataclasses.field(default=None, compare=False)
    line_code: str | None = dataclasses.field(default=None, compare=False)
    line_description: str | None = dataclasses.field(default=None, compare=False)
    contract_type: str | None = dataclasses.field(default=None, compare=False)
    term_of_agreement: int = dataclasses.field(default=0, compare=False)
    annual_mileage: float = dataclasses.field(default=0.0, compare=False)
    mileage_unit: str = dataclasses.field(default="Miles", compare=False)
    deposit: float = dataclasses.field(default=0.0, compare=False)
    sales_offer: float = dataclasses.field(default=0.0, compare=False)
    total_deposit: float = dataclasses.field(default=0.0, compare=False)
    number_of_installments: int = dataclasses.field(default=0, compare=False)
    monthly_rental_nlp: float = dataclasses.field(default=0.0, compare=False)
    monthly_rental_glp: float = dataclasses.field(default=0.0, compare=False)
    otr: float = dataclasses.field(default=0.0, compare=False)
    total_payable_amount: float = dataclasses.field(default=0.0, compare=False)
    total_credit_amount: float = dataclasses.field(default=0.0, compare=False)
    optional_final_payment: float = dataclasses.field(default=0.0, compare=False)
    option_purchase_fee: float = dataclasses.field(default=0.0, compare=False)
    apr: float = dataclasses.field(default=0.0, compare=False)
    fixed_roi: float = dataclasses.field(default=0.0, compare=False)
    excess_mileage: float = dataclasses.field(default=0.0, compare=False)
    option_type: str = dataclasses.field(default="", compare=False)
    option_description: str = dataclasses.field(default="", compare=False)
    option_gross_list_price: float = dataclasses.field(default=0.0, compare=False)
    last_scraped_on: str | None = dataclasses.field(compare=False, default=None)
    is_current: bool | None = dataclasses.field(compare=False, default=None)

    def __post_init__(self):
        self.recorded_at = current_timestamp_dashed_str_with_timezone()
        self.is_current = self._calculate_is_current()
        self.vehicle_id = self.calculate_vehicle_id()

        # validate required fields
        validate_not_blank_or_empty(self.recorded_at, "recorded_at")
        validate_not_blank_or_empty(self.vehicle_id, "vehicle_id")
        validate_not_blank_or_empty(self.market, "market")
        validate_not_blank_or_empty(self.vendor, "vendor")
        validate_not_blank_or_empty(self.series, "series")
        validate_not_blank_or_empty(self.model_range_code, "model_range_code")
        validate_not_blank_or_empty(
            self.model_range_description, "model_range_description"
        )
        validate_not_blank_or_empty(self.model_code, "model_code")
        validate_not_blank_or_empty(self.model_description, "model_description")
        validate_not_blank_or_empty(self.line_code, "line_code")
        validate_not_blank_or_empty(self.line_description, "line_description")
        validate_not_blank_or_empty(self.contract_type, "contract_type")

    def _calculate_is_current(self) -> bool | None:
        if self.last_scraped_on:
            # Since date represents when the item was last written to disk, instead of the true current date
            # We need to rely on another source of time, so we will currently use today's date to evaluate freshness
            return self.last_scraped_on == today_dashed_str()

        return None

    def calculate_vehicle_id(self) -> str:
        """Calculates the unique vehicle ID based on the given attributes."""
        # Concatenate relevant attributes
        data = f"{self.vendor}_{self.market}_{self.series}_{self.model_range_description}_{self.model_description}_{self.line_description}"

        # Calculate the hash using a chosen algorithm (Blake2b)
        hash_object = hashlib.blake2b(digest_size=4)
        hash_object.update(data.encode("utf-8"))
        hex_dig = hash_object.hexdigest()
        # limiting vendor name to 3 digits ex: aud, tes, bmw
        prefix_vendor = f"{self.vendor}"[:3]
        # Create the final identifier
        return f"{self.market}_{prefix_vendor}_{hex_dig}".lower()

    def pcp_difference_with(
        self, other: "FinanceLineItem"
    ) -> list[DifferenceFinanceItem]:

        differences: list[DifferenceFinanceItem] = []

        # Only compare line items for same car model
        if other != self:
            return differences

        # Check if self's monthly rental glp is different from other's
        if float(self.monthly_rental_glp) != float(other.monthly_rental_glp):
            differences.append(
                build_difference_for_finance_item(
                    finance_line_item=self,
                    new_value=float(self.monthly_rental_glp),
                    old_value=float(other.monthly_rental_glp),
                    reason=FinanceItemDifferenceReason.PCP_MONTHLY_RENTAL_CHANGED,
                )
            )

        if float(self.otr) != float(other.otr):
            differences.append(
                build_difference_for_finance_item(
                    finance_line_item=self,
                    new_value=float(self.otr),
                    old_value=float(other.otr),
                    reason=FinanceItemDifferenceReason.PCP_OTR_CHANGED,
                )
            )

        if float(self.apr) != float(other.apr):
            differences.append(
                build_difference_for_finance_item(
                    finance_line_item=self,
                    new_value=float(self.apr),
                    old_value=float(other.apr),
                    reason=FinanceItemDifferenceReason.PCP_APR_CHANGED,
                )
            )

        if float(self.sales_offer) != float(other.sales_offer):
            differences.append(
                build_difference_for_finance_item(
                    finance_line_item=self,
                    new_value=float(self.sales_offer),
                    old_value=float(other.sales_offer),
                    reason=FinanceItemDifferenceReason.PCP_SALES_OFFER_CHANGED,
                )
            )

        if float(self.fixed_roi) != float(other.fixed_roi):
            differences.append(
                build_difference_for_finance_item(
                    finance_line_item=self,
                    new_value=float(self.fixed_roi),
                    old_value=float(other.fixed_roi),
                    reason=FinanceItemDifferenceReason.PCP_FIXED_ROI_CHANGED,
                )
            )

        if float(self.optional_final_payment) != float(other.optional_final_payment):
            differences.append(
                build_difference_for_finance_item(
                    finance_line_item=self,
                    new_value=float(self.optional_final_payment),
                    old_value=float(other.optional_final_payment),
                    reason=FinanceItemDifferenceReason.PCP_OPTIONAL_FINAL_PAYMENT_CHANGED,
                )
            )

        return differences


def create_finance_line_item(
    vendor: Vendor,
    series: str,
    model_range_code: str,
    model_range_description: str,
    model_code: str,
    model_description: str,
    line_code: str,
    line_description: str,
    contract_type: str,
    monthly_rental_glp: float,
    monthly_rental_nlp: float,
    market: Market,
    option_type: str = "",
    option_description: str = "",
    term_of_agreement: int = 0,
    number_of_installments: int = 0,
    deposit: float = 0.0,
    total_deposit: float = 0.0,
    total_credit_amount: float = 0.0,
    total_payable_amount: float = 0.0,
    otr: float = 0.0,
    annual_mileage: float = 0.0,
    excess_mileage: float = 0.0,
    optional_final_payment: float = 0.0,
    apr: float = 0.0,
    fixed_roi: float = 0.0,
    sales_offer: float = 0.0,
    option_gross_list_price: float = 0.0,
    option_purchase_fee: float = 0.0,
    mileage_unit: str = "Miles",
):
    return FinanceLineItem(
        recorded_at=current_timestamp_dashed_str_with_timezone(),
        last_scraped_on=today_dashed_str(),
        vendor=vendor,
        series=series,
        model_range_code=model_range_code,
        model_range_description=model_range_description,
        model_code=model_code,
        model_description=model_description,
        line_code=line_code,
        line_description=line_description,
        contract_type=contract_type,
        monthly_rental_nlp=monthly_rental_nlp,
        monthly_rental_glp=monthly_rental_glp,
        currency=Currency[market],
        market=market,
        option_type=option_type,
        option_description=option_description,
        term_of_agreement=term_of_agreement,
        number_of_installments=number_of_installments,
        deposit=deposit,
        total_deposit=total_deposit,
        total_credit_amount=total_credit_amount,
        total_payable_amount=total_payable_amount,
        otr=otr,
        annual_mileage=annual_mileage,
        excess_mileage=excess_mileage,
        optional_final_payment=optional_final_payment,
        apr=apr,
        fixed_roi=fixed_roi,
        sales_offer=sales_offer,
        option_gross_list_price=option_gross_list_price,
        option_purchase_fee=option_purchase_fee,
        mileage_unit=mileage_unit,
    )
