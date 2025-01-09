from types import SimpleNamespace
from unittest.mock import patch

from test.price_monitor.utils.test_data_builder import (
    create_test_finance_line_item,
    create_test_line_item,
)

from src.price_monitor.finance_scraper.tesla.finance_parser import (
    parse_finance_line_items,
    parse_pcp_finance_details,
    parse_lowest_price_metallic_paint,
)
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.utils.clock import today_dashed_str


def test_parse_finance_line_items():
    expected_finance_line_item = create_test_finance_line_item(
        vendor=Vendor.TESLA,
        series="Z",
        model_range_code="G29",
        model_range_description="Tesla Z4",
        model_code="HF51",
        model_description="Tesla Z4 M40i - automatic",
        line_code="M_PERFORMANCE_LINE",
        line_description="M_PERFORMANCE_LINE",
        contract_type="Business Contract Hire",
        monthly_rental_glp=619,
        monthly_rental_nlp=515.83,
        market=Market.UK,
    )

    line_item = create_test_line_item(
        recorded_at=today_dashed_str(),
        vendor=Vendor.TESLA,
        series="Z",
        model_range_code="G29",
        model_range_description="Tesla Z4",
        model_code="HF51",
        model_description="Tesla Z4 M40i - automatic",
        line_code="M_PERFORMANCE_LINE",
        line_description="M_PERFORMANCE_LINE",
        currency="EUR",
        market=Market.UK,
        net_list_price=524,
        gross_list_price=813,
    )

    parsed_finance_line_item = parse_finance_line_items(
        [line_item], {"M_PERFORMANCE_LINE": {"Business Contract Hire": "£619 /mo"}}
    )

    assert expected_finance_line_item == parsed_finance_line_item[0]


@patch(
    "src.price_monitor.finance_scraper.tesla.finance_parser.parse_lowest_price_metallic_paint"
)
def test_parse_pcp_finance_line_items(mock_parse_lowest_price_metallic_paint):
    mock_parse_lowest_price_metallic_paint.return_value = {
        "paint_type": "PAINT",
        "paint_description": "Deep Blue Metallic",
        "paint_price": 1300,
    }
    expected_finance_line_item = create_test_finance_line_item(
        vendor=Vendor.TESLA,
        series="Z",
        model_range_code="G29",
        model_range_description="Tesla Z4",
        model_code="HF51",
        model_description="Tesla Z4 M40i - automatic",
        line_code="M_PERFORMANCE_LINE",
        line_description="M_PERFORMANCE_LINE",
        contract_type="PCP",
        monthly_rental_glp=619.0,
        monthly_rental_nlp=515.83,
        market=Market.UK,
        term_of_agreement=48,
        number_of_installments=48,
        otr=52990.0,
        deposit=4999,
        total_deposit=4950.0,
        total_credit_amount=48040.0,
        optional_final_payment=22786.0,
        fixed_roi=0.0,
        total_payable_amount=52990.0,
        apr=0.0,
        annual_mileage=10000.0,
        excess_mileage=14.0,
        option_type="PAINT",
        option_description="Deep Blue Metallic",
        option_gross_list_price=1300,
    )

    line_item = create_test_line_item(
        recorded_at=today_dashed_str(),
        vendor=Vendor.TESLA,
        series="Z",
        model_range_code="G29",
        model_range_description="Tesla Z4",
        model_code="HF51",
        model_description="Tesla Z4 M40i - automatic",
        line_code="M_PERFORMANCE_LINE",
        line_description="M_PERFORMANCE_LINE",
        currency="EUR",
        market=Market.UK,
        net_list_price=524,
        gross_list_price=813,
    )

    parsed_finance_line_item = parse_finance_line_items(
        [line_item],
        {
            "M_PERFORMANCE_LINE": {
                "PCP": {
                    "rental_th": "£619 /mo",
                    "details": "Representative Example | 48 fixed monthly payments of £526 | On-the-road cash price £52,990 | Total down payment £4,950 | Total amount of credit £48,040 | Optional Final Payment £22,786 | Interest charges £0 | Fixed rate of interest per year 0.00% | Length of agreement 48 months | Total amount payable £52,990 | Representative APR 0.00% | Mileage per annum 10,000 | Excess mileage charge 14 ppm (Plus VAT).",
                }
            }
        },
    )

    assert expected_finance_line_item == parsed_finance_line_item[0]


@patch(
    "src.price_monitor.finance_scraper.tesla.finance_parser.parse_lowest_price_metallic_paint"
)
def test_parse_business_pcp_finance_line_items(mock_parse_lowest_price_metallic_paint):
    mock_parse_lowest_price_metallic_paint.return_value = {
        "paint_type": "PAINT",
        "paint_description": "Deep Blue Metallic",
        "paint_price": 1300,
    }
    expected_finance_line_item = create_test_finance_line_item(
        vendor=Vendor.TESLA,
        series="Z",
        model_range_code="G29",
        model_range_description="Tesla Z4",
        model_code="HF51",
        model_description="Tesla Z4 M40i - automatic",
        line_code="M_PERFORMANCE_LINE",
        line_description="M_PERFORMANCE_LINE",
        contract_type="Business PCP",
        monthly_rental_glp=619.0,
        monthly_rental_nlp=515.83,
        market=Market.UK,
        term_of_agreement=48,
        number_of_installments=48,
        otr=52990.0,
        deposit=4999,
        total_deposit=4950.0,
        total_credit_amount=48040.0,
        optional_final_payment=22786.0,
        fixed_roi=0.0,
        total_payable_amount=52990.0,
        apr=0.0,
        annual_mileage=10000.0,
        excess_mileage=14.0,
        option_type="PAINT",
        option_description="Deep Blue Metallic",
        option_gross_list_price=1300,
    )

    line_item = create_test_line_item(
        recorded_at=today_dashed_str(),
        vendor=Vendor.TESLA,
        series="Z",
        model_range_code="G29",
        model_range_description="Tesla Z4",
        model_code="HF51",
        model_description="Tesla Z4 M40i - automatic",
        line_code="M_PERFORMANCE_LINE",
        line_description="M_PERFORMANCE_LINE",
        currency="EUR",
        market=Market.UK,
        net_list_price=524,
        gross_list_price=813,
    )

    parsed_finance_line_item = parse_finance_line_items(
        [line_item],
        {
            "M_PERFORMANCE_LINE": {
                "Business PCP": {
                    "rental_th": "£619 /mo",
                    "details": "Representative Example | 48 fixed monthly payments of £526 | On-the-road cash price £52,990 | Total down payment £4,950 | Total amount of credit £48,040 | Optional Final Payment £22,786 | Interest charges £0 | Fixed rate of interest per year 0.00% | Length of agreement 48 months | Total amount payable £52,990 | Representative APR 0.00% | Mileage per annum 10,000 | Excess mileage charge 14 ppm (Plus VAT).",
                }
            }
        },
    )

    assert expected_finance_line_item == parsed_finance_line_item[0]


def test_parse_pcp_finance_details():
    pcp_details = (
        "Representative Example | 48 fixed monthly payments of £526 | On-the-road cash price £52,"
        "990 | Total down payment £4,950 | Total amount of credit £48,040 | Optional Final Payment £22,"
        "786 | Interest charges £0 | Fixed rate of interest per year 0.00% | Length of agreement 48 months "
        "| Total amount payable £52,990 | Representative APR 0.00% | Mileage per annum 10,000 | Excess "
        "mileage charge 14 ppm (Plus VAT)."
    )

    expected_finance_details = {
        "annual_mileage": "10000",
        "apr": "0.00",
        "excess_mileage": "14",
        "number_of_installments": "48",
        "fixed_roi": "0.00",
        "interest_charges": "0",
        "optional_final_payment": "22786",
        "otr": "52990",
        "term_of_agreement": "48",
        "total_credit_amount": "48040",
        "total_deposit": "4950",
        "total_payable_amount": "52990",
    }

    actual_finance_details = parse_pcp_finance_details(pcp_details)

    assert expected_finance_details == actual_finance_details


def test_get_number_of_installments_type_issue_returns_zero():
    expected_number_of_installments = 0

    pcp_details = (
        "Representative Example | abc fixed monthly payments of £526 | On-the-road cash price £52,"
        "990 | Total down payment £4,950 | Total amount of credit £48,040 | Optional Final Payment £22,"
        "786 | Interest charges £0 | Fixed rate of interest per year 0.00% | Length of agreement 48 months "
        "| Total amount payable £52,990 | Representative APR 0.00% | Mileage per annum 10,000 | Excess "
        "mileage charge 14 ppm (Plus VAT)."
    )
    actual_finance_details = parse_pcp_finance_details(pcp_details)
    actual_number_of_installments = actual_finance_details["number_of_installments"]

    assert expected_number_of_installments == actual_number_of_installments


def test_get_number_of_installments_key_issue_returns_zero():
    expected_number_of_installments = 0

    pcp_details = (
        "Representative Example | On-the-road cash price £52,990 | Total down payment £4,950 | Total amount "
        "of credit £48,040 | Optional Final Payment £22,786 | Interest charges £0 | Fixed rate of interest "
        "per year 0.00% | Length of agreement 48 months | Total amount payable £52,990 | Representative "
        "APR 0.00% | Mileage per annum 10,000 | Excess mileage charge 14 ppm (Plus VAT)."
    )
    actual_finance_details = parse_pcp_finance_details(pcp_details)
    actual_number_of_installments = actual_finance_details["number_of_installments"]

    assert expected_number_of_installments == actual_number_of_installments


def test_parse_lowest_price_metallic_paint_with_mock():

    line_option_codes = [
        SimpleNamespace(
            code="$JSBA", type="Standard Paint", description="Red", gross_list_price=500
        ),
        SimpleNamespace(
            code="$ASJM",
            type="Metallic Paint",
            description="Silver",
            gross_list_price=1000,
        ),
        SimpleNamespace(
            code="$PPSB",
            type="Metallic Paint",
            description="Deep Blue",
            gross_list_price=1300,
        ),
        SimpleNamespace(
            code="$PMAT",
            type="Premium Paint",
            description="Black",
            gross_list_price=1500,
        ),
    ]

    expected_result = {
        "paint_type": "Metallic Paint",
        "paint_description": "Deep Blue",
        "paint_price": 1300,
    }

    result = parse_lowest_price_metallic_paint(line_option_codes)

    assert result == expected_result
