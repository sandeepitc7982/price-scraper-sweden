from test.price_monitor.utils.test_data_builder import (
    create_test_finance_line_item,
    create_test_line_item,
)

from src.price_monitor.finance_scraper.bmw.finance_parser import parse_finance_line_item
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.utils.clock import today_dashed_str


def test_parse_finance_line_item():
    expected_finance_line_item = create_test_finance_line_item(
        vendor=Vendor.BMW,
        series="Z",
        model_range_code="G29",
        model_range_description="BMW Z4",
        model_code="HF51",
        model_description="BMW Z4 M40i - automatic",
        line_code="M_PERFORMANCE_LINE",
        line_description="M_PERFORMANCE_LINE",
        contract_type="PCP",
        monthly_rental_nlp=410.83,
        monthly_rental_glp=493.0,
        market=Market.UK,
    )

    line_item = create_test_line_item(
        recorded_at=today_dashed_str(),
        vendor=Vendor.BMW,
        series="Z",
        model_range_code="G29",
        model_range_description="BMW Z4",
        model_code="HF51",
        model_description="BMW Z4 M40i - automatic",
        line_code="M_PERFORMANCE_LINE",
        line_description="M_PERFORMANCE_LINE",
        currency="EUR",
        market=Market.UK,
        net_list_price=56218.49,
        gross_list_price=66900.0,
    )

    parsed_finance_line_item = parse_finance_line_item(line_item, "PCP", 493)

    assert expected_finance_line_item == parsed_finance_line_item
