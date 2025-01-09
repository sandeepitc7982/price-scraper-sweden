from typing import List

from src.price_monitor.finance_comparer.difference_finance_item import (
    DifferenceFinanceItem,
    FinanceItemDifferenceReason,
)
from src.price_monitor.model.difference_item import DifferenceItem, DifferenceReason
from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.option_price_difference_item import (
    OptionPriceDifferenceItem,
    OptionPriceDifferenceReason,
)
from src.price_monitor.model.price_difference_item import (
    PriceDifferenceItem,
    PriceDifferenceReason,
)
from src.price_monitor.model.vendor import Currency, Market, Vendor
from src.price_monitor.price_scraper.constants import NOT_AVAILABLE
from src.price_monitor.utils.clock import (
    today_dashed_str,
    yesterday_dashed_str_with_key,
)


def create_test_line_item(
    recorded_at: str = yesterday_dashed_str_with_key(),
    vendor: Vendor = Vendor.AUDI,
    market: Market = Market.NL,
    series: str = "test",
    model_range_code: str = "test",
    model_range_description: str = "test",
    model_code: str = "test",
    model_description: str = "test",
    line_code: str = "test",
    line_description: str = "test",
    line_option_codes: List[LineItemOptionCode] = [],
    currency: str = "test",
    net_list_price: float = 0.0,
    gross_list_price: float = 0.0,
    on_the_road_price: float = 0.0,
    engine_performance_kw: str = NOT_AVAILABLE,
    last_scraped_on: str | None = None,
):
    return LineItem(
        recorded_at=recorded_at,
        vendor=vendor,
        series=series,
        model_range_code=model_range_code,
        model_range_description=model_range_description,
        model_code=model_code,
        model_description=model_description,
        line_code=line_code,
        line_description=line_description,
        line_option_codes=line_option_codes,
        currency=currency,
        net_list_price=net_list_price,
        gross_list_price=gross_list_price,
        on_the_road_price=on_the_road_price,
        market=market,
        engine_performance_kw=engine_performance_kw,
        last_scraped_on=last_scraped_on,
    )


def create_difference_line_item(
    recorded_at: str = today_dashed_str(),
    vendor: Vendor = Vendor.AUDI,
    series: str = "test",
    model_range_code: str = "test",
    model_range_description: str = "test",
    model_code: str = "test",
    model_description: str = "test",
    line_code: str = "test",
    line_description: str = "test",
    old_value: str = "",
    new_value: str = "",
    reason: DifferenceReason = DifferenceReason.NEW_LINE,
    market: Market = Market.NL,
):
    return DifferenceItem(
        recorded_at,
        vendor,
        series,
        model_range_code,
        model_range_description,
        model_code,
        model_description,
        line_code,
        line_description,
        old_value,
        new_value,
        reason,
        market,
    )


def assert_line_items_list(
    expected_line_item_list: list[LineItem], actual_line_item_list: list[LineItem]
):
    for i in range(0, len(expected_line_item_list)):
        assert_line_items_fields(expected_line_item_list[i], actual_line_item_list[i])


def assert_line_items_fields(expected_line_item: LineItem, actual_line_item: LineItem):
    assert expected_line_item.vendor == actual_line_item.vendor
    assert expected_line_item.series == actual_line_item.series
    assert expected_line_item.model_range_code == actual_line_item.model_range_code
    assert (
        expected_line_item.model_range_description
        == actual_line_item.model_range_description
    )
    assert expected_line_item.model_code == actual_line_item.model_code
    assert expected_line_item.model_description == actual_line_item.model_description
    assert expected_line_item.line_code == actual_line_item.line_code
    assert expected_line_item.line_description == actual_line_item.line_description
    assert expected_line_item.line_option_codes == actual_line_item.line_option_codes
    assert expected_line_item.currency == actual_line_item.currency
    assert expected_line_item.net_list_price == actual_line_item.net_list_price
    assert expected_line_item.gross_list_price == actual_line_item.gross_list_price
    assert expected_line_item.market == actual_line_item.market
    assert (
        expected_line_item.engine_performance_kw
        == actual_line_item.engine_performance_kw
    )
    assert (
        expected_line_item.engine_performance_hp
        == actual_line_item.engine_performance_hp
    )


def create_test_line_item_option_code(
    code: str = "",
    type: str = "",
    description: str = "",
    net_list_price: float = 0.00,
    gross_list_price: float = 0.00,
    included: bool = True,
    category: str = "",
):
    return LineItemOptionCode(
        code=code,
        type=type,
        description=description,
        net_list_price=net_list_price,
        gross_list_price=gross_list_price,
        included=included,
        predicted_category=category,
    )


def create_test_difference_item(
    line_item: LineItem = create_test_line_item(),
    old_price: float = 0,
    new_price: float = 0,
    perc_change: str = "0%",
    model_price_change: float = 0.0,
    reason: PriceDifferenceReason = PriceDifferenceReason.NO_REASON,
    option_code: str = "",
    option_gross_list_price: float = 0.00,
    option_net_list_price: float = 0.00,
):
    return PriceDifferenceItem(
        recorded_at=today_dashed_str(),
        vendor=line_item.vendor,
        series=line_item.series,
        model_range_code=line_item.model_range_code,
        model_range_description=line_item.model_range_description,
        model_code=line_item.model_code,
        model_description=line_item.model_description,
        line_code=line_item.line_code,
        line_description=line_item.line_description,
        market=line_item.market,
        old_price=old_price,
        new_price=new_price,
        currency="EUR",
        perc_change=perc_change,
        model_price_change=model_price_change,
        reason=reason,
        option_code=option_code,
        option_gross_list_price=option_gross_list_price,
        option_net_list_price=option_net_list_price,
    )


def create_test_option_price_difference_item(
    date: str = today_dashed_str(),
    vendor: Vendor = "audi",
    market: Market = "DE",
    option_description: str = "",
    option_old_price: float = 0.00,
    option_new_price: float = 0.00,
    currency: str = "",
    perc_change: str = "",
    option_price_change: float = 0.00,
    reason: OptionPriceDifferenceReason = OptionPriceDifferenceReason.PRICE_DECREASE,
    model_range_description: str = "",
) -> OptionPriceDifferenceItem:
    return OptionPriceDifferenceItem(
        recorded_at=date,
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


def create_test_finance_line_item(
    vehicle_id: str = "uk_aud_dc07c121",
    vendor: Vendor = "audi",
    series: str = "test",
    model_range_code: str = "test",
    model_range_description: str = "test",
    model_code: str = "test",
    model_description: str = "test",
    line_code: str = "test",
    line_description: str = "test",
    contract_type: str = "test",
    monthly_rental_nlp: float = 0.0,
    monthly_rental_glp: float = 0.0,
    market: Market = "DE",
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
    date: str = today_dashed_str(),
    last_scraped_on: str | None = today_dashed_str(),
) -> FinanceLineItem:
    return FinanceLineItem(
        recorded_at=date,
        vehicle_id=vehicle_id,
        last_scraped_on=last_scraped_on,
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
        option_description=option_description,
        option_type=option_type,
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
        option_purchase_fee=option_purchase_fee,
        option_gross_list_price=option_gross_list_price,
    )


def create_difference_finance_line_item(
    date: str = today_dashed_str(),
    vehicle_id: str = "test",
    vendor: Vendor = Vendor.AUDI,
    series: str = "test",
    model_range_code: str = "test",
    model_range_description: str = "test",
    model_code: str = "test",
    model_description: str = "test",
    line_code: str = "test",
    line_description: str = "test",
    contract_type: str = "PCP",
    old_value: float = 0.0,
    new_value: float = 0.0,
    reason: FinanceItemDifferenceReason = FinanceItemDifferenceReason.PCP_OTR_CHANGED,
    market: Market = Market.DE,
):
    return DifferenceFinanceItem(
        date,
        vehicle_id,
        vendor,
        series,
        model_range_code,
        model_range_description,
        model_code,
        model_description,
        line_code,
        line_description,
        contract_type,
        market,
        old_value,
        new_value,
        reason,
    )
