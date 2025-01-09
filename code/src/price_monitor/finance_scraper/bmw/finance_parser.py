from src.price_monitor.model.finance_line_item import create_finance_line_item
from src.price_monitor.model.vendor import Market, Vendor, compute_net_list_price


def parse_finance_line_item(line_item, contract_type, monthly_payment):
    monthly_payment = float(monthly_payment)
    line_item = create_finance_line_item(
        vendor=Vendor.BMW,
        series=line_item.series,
        model_range_code=line_item.model_range_code,
        model_range_description=line_item.model_range_description,
        model_code=line_item.model_code,
        model_description=line_item.model_description,
        line_code=line_item.line_code,
        line_description=line_item.line_description,
        contract_type=contract_type,
        monthly_rental_nlp=compute_net_list_price(Market.UK, monthly_payment),
        monthly_rental_glp=monthly_payment,
        market=Market.UK,
    )
    return line_item


def parse_finance_line_item_for_pcp(
    line_item, product_id, parameters, lowest_price_metallic_paint_option_details
):
    params = {}
    for parameter in parameters:
        params[parameter["id"]] = parameter["value"]
    monthly_rental_glp = params["installment/grossAmount"]
    monthly_rental_nlp = compute_net_list_price(Market.UK, monthly_rental_glp)
    return create_finance_line_item(
        vendor=Vendor.BMW,
        series=line_item.series,
        model_range_code=line_item.model_range_code,
        model_range_description=line_item.model_range_description,
        model_code=line_item.model_code,
        model_description=line_item.model_description,
        line_code=line_item.line_code,
        line_description=line_item.line_description,
        contract_type=product_id,
        monthly_rental_nlp=monthly_rental_nlp,
        monthly_rental_glp=monthly_rental_glp,
        market=Market.UK,
        term_of_agreement=int(params["term"]),
        number_of_installments=int(params["installmentPeriodCount"]),
        deposit=params["downPaymentAmount/grossAmount"],
        total_deposit=params["totalDeposit/grossAmount"],
        total_credit_amount=params["financeAmount/grossAmount"],
        total_payable_amount=params["sumOfAllPayments/grossAmount"],
        otr=params["calculatedVehicleAmount/grossAmount"],
        annual_mileage=params["annualMileage"],
        excess_mileage=params["excessContractualMileageAmount/grossAmount"],
        optional_final_payment=params["residualValueAmount/grossAmount"],
        apr=params["interestEffective"] * 100,
        fixed_roi=params["interestEffective"] * 100,
        sales_offer=params["depositContribution/grossAmount"],
        option_gross_list_price=lowest_price_metallic_paint_option_details[
            "paint_price"
        ],
        option_type=lowest_price_metallic_paint_option_details["option_type"],
        option_description=lowest_price_metallic_paint_option_details[
            "paint_description"
        ],
    )
