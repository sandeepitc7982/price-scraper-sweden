import re

from loguru import logger

from src.price_monitor.model.finance_line_item import create_finance_line_item
from src.price_monitor.model.vendor import Market, Vendor, compute_net_list_price


def parse_available_model_ranges_for_finance(models_json: dict) -> list:
    model_details = []
    for model in models_json["data"]["carlineStructure"]["carlineGroups"]:
        for carline in model["carlines"]:
            if carline["identifier"].get("active"):
                model_detail = {
                    "series": model["name"],
                    "model_range_description": carline["name"],
                    "model_range_code": carline["identifier"]["id"],
                }
                model_details.append(model_detail)
    return model_details


def parse_finance_options(finance_options_json: dict) -> list:
    finance_options = []
    products = finance_options_json["Response"]["Products"]["Product"]
    if isinstance(products, dict):
        products = [products]
    for finance_option in products:
        finance_options.append(
            {"finance_code": finance_option["@ID"], "name": finance_option["Label"]}
        )
    return finance_options


def parse_finance_option_details(finance_option_details_json: dict) -> dict:
    payment_details = finance_option_details_json["Response"].get("Calculation", {})

    response = {
        "monthly_payment": payment_details.get("InstallmentGrossAmount", {}).get(
            "@Value", 0.0
        ),
        "down_payment": payment_details.get("DownPayment", {}).get("@Value", 0.0),
    }
    return response


def parse_finance_line_item(finance_option, finance_option_details, model):
    extracted_model = model.copy()
    extracted_model["finance_name"] = finance_option["name"]
    extracted_model["monthly_payment"] = float(
        finance_option_details["monthly_payment"]
    )
    extracted_model["down_payment"] = finance_option_details["down_payment"]
    line_item = create_finance_line_item(
        vendor=Vendor.AUDI,
        series=extracted_model["series"],
        model_range_code=extracted_model["model_range_code"],
        model_range_description=extracted_model["model_range_description"],
        model_code=extracted_model["model_code"],
        model_description=extracted_model["model_description"],
        line_code=extracted_model["line_code"],
        line_description=extracted_model["line_description"],
        contract_type=extracted_model["finance_name"],
        monthly_rental_nlp=compute_net_list_price(
            Market.UK, extracted_model["monthly_payment"]
        ),
        monthly_rental_glp=extracted_model["monthly_payment"],
        market=Market.UK,
    )
    return line_item


# Extracting PCP options from the response.
# eg: sales_offer = finance_option_details_json["Response"]["Calculation"]["BrandDownPayment"]["Value"]
#     response = {
#         sales_offer = 1234,
#     }
def parse_pcp_finance_option_details(finance_option_details_json: dict) -> dict:
    number_of_installments = _get_number_of_installments(finance_option_details_json)
    details_list = finance_option_details_json["Response"]["Calculation"]

    response = {
        "monthly_payment": details_list.get("InstallmentGrossAmount", {}).get(
            "@Value", 0.0
        ),
        "down_payment": details_list.get("DownPayment", {}).get("@Value", 0.0),
        "sales_offer": details_list.get("BrandDownPayment", {}).get("@Value", 0.0),
        # .get -> response will not fail if one of the value in dict fails
        "deposit": details_list.get("DownPayment", {}).get("@Value", 0.0),
        "total_deposit": details_list.get("TotalDownPayment", {}).get("@Value", 0.0),
        "total_credit_amount": details_list.get("NetCreditAmount", {}).get(
            "@Value", 0.0
        ),
        "total_payable_amount": details_list.get("GrossCreditAmount", {}).get(
            "@Value", 0.0
        ),
        "otr": details_list.get("PurchasePrice", {}).get("@Value", 0.0),
        "annual_mileage": details_list.get("Mileage", {}).get("@Value", 0.0),
        "excess_mileage": details_list.get("UpperMileageRateTotalGrossAmount", {}).get(
            "@Value", 0.0
        ),
        "optional_final_payment": details_list.get("FinalPayment", {}).get(
            "@Value", 0.0
        ),
        "fixed_roi": details_list.get("InterestRateNominal", {}).get("@Value", 0.0),
        "apr": details_list.get("InterestRateEffective", {}).get("@Value", 0.0),
        "option_purchase_fee": details_list.get("BuyBackFeeAmount", {}).get(
            "@Value", 0.0
        ),
        "term_of_agreement": details_list.get("Duration", {}).get("@Value", 0),
        "number_of_installments": number_of_installments,
    }

    return response


def _get_number_of_installments(finance_option_details_json: dict) -> int:
    try:
        parameters = finance_option_details_json["Response"]["Parameters"]["Group"][
            "Parameter"
        ]
        rate_label = ""
        for parameter in parameters:
            if parameter.get("@ID") == "Rate":
                rate_label = parameter.get("Label")
        match = re.search(r"\d+", rate_label)
        if not match:
            raise ValueError("No numeric value found in rate label")
        number_of_installments = int(match.group())
        return number_of_installments
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Error extracting number_of_installments: {e}, falling back to 0")
        return 0


# Creating line item from the extracted PCP data
def parse_pcp_finance_line_item(finance_option_details, model):
    extracted_model = model.copy()
    extracted_model["monthly_payment"] = float(
        finance_option_details["monthly_payment"]
    )
    extracted_model["down_payment"] = finance_option_details["down_payment"]
    extracted_model["sales_offer"] = finance_option_details["sales_offer"]
    line_item = create_finance_line_item(
        vendor=Vendor.AUDI,
        series=extracted_model["series"],
        model_range_code=extracted_model["model_range_code"],
        model_range_description=extracted_model["model_range_description"],
        model_code=extracted_model["model_code"],
        model_description=extracted_model["model_description"],
        line_code=extracted_model["line_code"],
        line_description=extracted_model["line_description"],
        contract_type="PCP",  # Always PCP instead of the PCP Contract Type text in the Audi website
        monthly_rental_nlp=compute_net_list_price(
            Market.UK, extracted_model["monthly_payment"]
        ),
        monthly_rental_glp=extracted_model["monthly_payment"],
        market=Market.UK,
        option_type=extracted_model["default_configured_car_options"]["option_type"],
        option_description=extracted_model["default_configured_car_options"][
            "option_description"
        ],
        sales_offer=extracted_model["sales_offer"],
        deposit=finance_option_details["deposit"],
        total_deposit=finance_option_details["total_deposit"],
        total_credit_amount=finance_option_details["total_credit_amount"],
        total_payable_amount=finance_option_details["total_payable_amount"],
        otr=finance_option_details["otr"],
        annual_mileage=finance_option_details["annual_mileage"],
        excess_mileage=finance_option_details["excess_mileage"],
        optional_final_payment=finance_option_details["optional_final_payment"],
        apr=finance_option_details["apr"],
        fixed_roi=finance_option_details["fixed_roi"],
        option_purchase_fee=finance_option_details["option_purchase_fee"],
        term_of_agreement=finance_option_details["term_of_agreement"],
        option_gross_list_price=extracted_model["default_configured_car_options"][
            "option_gross_list_price"
        ],
        number_of_installments=finance_option_details["number_of_installments"],
    )
    return line_item


def parse_model_price(trimline):
    other_price = 0
    prices = trimline["defaultConfiguredCar"]["prices"]["priceParts"]
    for price in prices:
        if price["type"] == "financeableTotal":
            return price["price"]["value"]
        if price["type"] == "rotr":
            other_price = price["price"]["value"]
    return other_price


# extracting add on option details from the response
# eg: configured_options = {
#                 "option_type": "paint-metallic",
#                 "option_description": "Pearl white",
#                 "option_gross_list_price": 567,
#                 }
def parse_addon_options(trimline):
    configured_car_options_list = trimline["defaultConfiguredCar"]["catalog"][
        "features"
    ]["data"]
    configured_options = {}
    for option in configured_car_options_list:
        configured_options.update(
            {
                "option_type": option["family"]["id"],
                "option_description": option["name"],
                "option_gross_list_price": option["price"]["value"],
            }
        )
    return configured_options
