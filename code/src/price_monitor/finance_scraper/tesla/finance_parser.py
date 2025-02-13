import re

from loguru import logger

from src.price_monitor.finance_scraper.tesla.constants import (
    DEPOSIT,
    METALLIC_PAINT_CODE,
)
from src.price_monitor.model.finance_line_item import create_finance_line_item
from src.price_monitor.model.vendor import Market, Vendor, compute_net_list_price


def parse_lowest_price_metallic_paint(line_option_codes):
    lowest_price_metallic_paint = {}
    for option in line_option_codes:
        if option.code == METALLIC_PAINT_CODE or option.code == "$PBSB":
            lowest_price_metallic_paint = {
                "paint_type": option.type,
                "paint_description": option.description,
                "paint_price": option.gross_list_price,
            }

    return lowest_price_metallic_paint


def parse_finance_line_items(line_items, finance_details):
    finance_line_items = []
    for line_item in line_items:
        for contract_type, finance_option_details in finance_details[
            line_item.line_code
        ].items():
            if finance_option_details is None:
                continue

            if contract_type == "PCP" or contract_type == "Business PCP":
                monthly_payment = float(
                    finance_option_details["rental_th"][1:-4].replace(",", "")
                )
                pcp_details = parse_pcp_finance_details(
                    finance_option_details["details"]
                )
                lowest_price_metallic_paint = parse_lowest_price_metallic_paint(
                    line_item.line_option_codes
                )
                finance_line_items.append(
                    create_finance_line_item(
                        vendor=Vendor.TESLA,
                        series=line_item.series,
                        model_range_code=line_item.model_range_code,
                        model_range_description=line_item.model_range_description,
                        model_code=line_item.model_code,
                        model_description=line_item.model_description,
                        line_code=line_item.line_code,
                        line_description=line_item.line_description,
                        contract_type=contract_type,
                        monthly_rental_nlp=compute_net_list_price(
                            Market.UK, monthly_payment
                        ),
                        monthly_rental_glp=monthly_payment,
                        market=Market.UK,
                        term_of_agreement=int(pcp_details["term_of_agreement"]),
                        number_of_installments=int(
                            pcp_details["number_of_installments"]
                        ),
                        otr=float(pcp_details["otr"]),
                        deposit=DEPOSIT,
                        total_deposit=float(pcp_details["total_deposit"]),
                        total_credit_amount=float(pcp_details["total_credit_amount"]),
                        optional_final_payment=float(
                            pcp_details["optional_final_payment"]
                        ),
                        fixed_roi=float(pcp_details["fixed_roi"]),
                        total_payable_amount=float(pcp_details["total_payable_amount"]),
                        apr=float(pcp_details["apr"]),
                        annual_mileage=float(pcp_details["annual_mileage"]),
                        excess_mileage=float(pcp_details["excess_mileage"]),
                        option_type=lowest_price_metallic_paint["paint_type"],
                        option_description=lowest_price_metallic_paint[
                            "paint_description"
                        ],
                        option_gross_list_price=lowest_price_metallic_paint[
                            "paint_price"
                        ],
                    )
                )
                continue

            monthly_payment = float(finance_option_details[1:-4].replace(",", ""))
            finance_line_items.append(
                create_finance_line_item(
                    vendor=Vendor.TESLA,
                    series=line_item.series,
                    model_range_code=line_item.model_range_code,
                    model_range_description=line_item.model_range_description,
                    model_code=line_item.model_code,
                    model_description=line_item.model_description,
                    line_code=line_item.line_code,
                    line_description=line_item.line_description,
                    contract_type=contract_type,
                    monthly_rental_nlp=compute_net_list_price(
                        Market.UK, monthly_payment
                    ),
                    monthly_rental_glp=monthly_payment,
                    market=Market.UK,
                )
            )
    return finance_line_items


def parse_pcp_finance_details(pcp_details: str):
    # Dictionary to store the extracted values
    pcp_finance_options = {}

    # Define a pattern to match the relevant information
    patterns = {
        "number_of_installments": r"(\d+) fixed monthly payments",
        "otr": r"On-the-road cash price £([\d,]+)",
        "total_deposit": r"Total down payment £([\d,]+)",
        "total_credit_amount": r"Total amount of credit £([\d,]+)",
        "optional_final_payment": r"Optional Final Payment £([\d,]+)",
        "interest_charges": r"Interest charges £([\d,]+)",
        "fixed_roi": r"Fixed rate of interest per year ([\d.]+%)",
        "term_of_agreement": r"Length of agreement (\d+) months",
        "total_payable_amount": r"Total amount payable £([\d,]+)",
        "apr": r"Representative APR ([\d.]+%)",
        "annual_mileage": r"Mileage per annum ([\d,]+)",
        "excess_mileage": r"Excess mileage charge (\d+) ppm",
    }

    # Extract values based on defined patterns
    for key, pattern in patterns.items():
        try:
            match = re.search(pattern, pcp_details)
            if match:
                # Handle percentage values by stripping '%' character
                if "%" in match.group(0):
                    pcp_finance_options[key] = match.group(1).replace("%", "")
                else:
                    # Clean numerical values by removing commas
                    pcp_finance_options[key] = match.group(1).replace(",", "")
            else:
                raise ValueError(f"Something went wrong, No match found for {key}")
        except Exception as e:
            logger.error(
                f"Unable to fetch value for {key} because of reason: {e}, falling back to 0"
            )
            pcp_finance_options[key] = 0
    return pcp_finance_options
