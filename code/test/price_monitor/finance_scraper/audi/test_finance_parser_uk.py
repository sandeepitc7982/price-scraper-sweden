import json
from pathlib import Path
from test.price_monitor.utils.test_data_builder import create_test_finance_line_item

from src.price_monitor.finance_scraper.audi.finance_parser_uk import (
    _get_number_of_installments,
    parse_addon_options,
    parse_available_model_ranges_for_finance,
    parse_finance_line_item,
    parse_finance_option_details,
    parse_finance_options,
    parse_model_price,
    parse_pcp_finance_line_item,
    parse_pcp_finance_option_details,
)
from src.price_monitor.model.vendor import Market, Vendor

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"
VENDOR = Vendor.AUDI


def test_parse_available_models_for_finance():
    expected_list_of_models = [
        {
            "model_range_code": "etrongt",
            "model_range_description": "e-tron GT quattro",
            "series": "e-tron GT",
        },
        {
            "model_range_code": "rsetrongt",
            "model_range_description": "RS e-tron GT",
            "series": "e-tron GT",
        },
        {
            "model_range_code": "a1sb",
            "model_range_description": "A1 Sportback",
            "series": "A1",
        },
        {
            "model_range_code": "a3sb",
            "model_range_description": "A3 Sportback",
            "series": "A3",
        },
        {
            "model_range_code": "a3sbetron",
            "model_range_description": "A3 Sportback TFSI e",
            "series": "A3",
        },
        {
            "model_range_code": "a3limo",
            "model_range_description": "A3 Saloon",
            "series": "A3",
        },
        {
            "model_range_code": "s3limo",
            "model_range_description": "S3 Saloon",
            "series": "A3",
        },
        {
            "model_range_code": "s3sb",
            "model_range_description": "S3 Sportback",
            "series": "A3",
        },
        {
            "model_range_code": "rs3sb",
            "model_range_description": "RS 3 Sportback",
            "series": "A3",
        },
        {
            "model_range_code": "rs3limo",
            "model_range_description": "RS 3 Saloon",
            "series": "A3",
        },
        {
            "model_range_code": "a4limo",
            "model_range_description": "A4 Saloon",
            "series": "A4",
        },
        {
            "model_range_code": "a4avant",
            "model_range_description": "A4 Avant",
            "series": "A4",
        },
        {
            "model_range_code": "rs4avant",
            "model_range_description": "RS 4 Avant",
            "series": "A4",
        },
        {
            "model_range_code": "a5coupe",
            "model_range_description": "A5 Coupé",
            "series": "A5",
        },
        {
            "model_range_code": "a5sb",
            "model_range_description": "A5 Sportback",
            "series": "A5",
        },
        {
            "model_range_code": "rs5coupe",
            "model_range_description": "RS 5 Coupé",
            "series": "A5",
        },
        {
            "model_range_code": "rs5sb",
            "model_range_description": "RS 5 Sportback",
            "series": "A5",
        },
        {
            "model_range_code": "a6limo",
            "model_range_description": "A6 Saloon",
            "series": "A6",
        },
        {
            "model_range_code": "a6limoetron",
            "model_range_description": "A6 Saloon TFSI e",
            "series": "A6",
        },
        {
            "model_range_code": "a6avant",
            "model_range_description": "A6 Avant",
            "series": "A6",
        },
        {
            "model_range_code": "a6avantetron",
            "model_range_description": "A6 Avant TFSI e",
            "series": "A6",
        },
        {
            "model_range_code": "s6limo",
            "model_range_description": "S6 Saloon",
            "series": "A6",
        },
        {
            "model_range_code": "s6avant",
            "model_range_description": "S6 Avant",
            "series": "A6",
        },
        {
            "model_range_code": "rs6avant",
            "model_range_description": "RS 6 Avant",
            "series": "A6",
        },
        {
            "model_range_code": "a7sb",
            "model_range_description": "A7 Sportback",
            "series": "A7",
        },
        {
            "model_range_code": "a7sbetron",
            "model_range_description": "A7 Sportback TFSI e",
            "series": "A7",
        },
        {
            "model_range_code": "s7sb",
            "model_range_description": "S7 Sportback",
            "series": "A7",
        },
        {
            "model_range_code": "rs7sb",
            "model_range_description": "RS 7 Sportback",
            "series": "A7",
        },
        {"model_range_code": "a8", "model_range_description": "A8", "series": "A8"},
        {
            "model_range_code": "a8etron",
            "model_range_description": "A8 TFSI e",
            "series": "A8",
        },
        {"model_range_code": "a8l", "model_range_description": "A8 L", "series": "A8"},
        {
            "model_range_code": "a8letron",
            "model_range_description": "A8 L TFSI e",
            "series": "A8",
        },
        {"model_range_code": "s8", "model_range_description": "S8", "series": "A8"},
        {"model_range_code": "q2", "model_range_description": "Q2", "series": "Q2"},
        {"model_range_code": "sq2", "model_range_description": "SQ2", "series": "Q2"},
        {"model_range_code": "q3", "model_range_description": "Q3", "series": "Q3"},
        {
            "model_range_code": "q3etron",
            "model_range_description": "Q3 TFSI e",
            "series": "Q3",
        },
        {
            "model_range_code": "q3sb",
            "model_range_description": "Q3 Sportback",
            "series": "Q3",
        },
        {
            "model_range_code": "q3sbetron",
            "model_range_description": "Q3 Sportback TFSI e",
            "series": "Q3",
        },
        {
            "model_range_code": "q4etron",
            "model_range_description": "Q4 e-tron",
            "series": "Q4 e-tron",
        },
        {
            "model_range_code": "q4sbetron",
            "model_range_description": "Q4 Sportback e-tron",
            "series": "Q4 e-tron",
        },
        {"model_range_code": "q5", "model_range_description": "Q5", "series": "Q5"},
        {
            "model_range_code": "q5etron",
            "model_range_description": "Q5 TFSI e",
            "series": "Q5",
        },
        {
            "model_range_code": "q5sb",
            "model_range_description": "Q5 Sportback",
            "series": "Q5",
        },
        {
            "model_range_code": "q5sbetron",
            "model_range_description": "Q5 Sportback TFSI e",
            "series": "Q5",
        },
        {
            "model_range_code": "q6etron",
            "model_range_description": "Q6 e-tron",
            "series": "Q6 e-tron",
        },
        {
            "model_range_code": "sq6etron",
            "model_range_description": "SQ6 e-tron",
            "series": "Q6 e-tron",
        },
        {"model_range_code": "q7", "model_range_description": "Q7 SUV", "series": "Q7"},
        {
            "model_range_code": "sq7",
            "model_range_description": "SQ7 SUV",
            "series": "Q7",
        },
        {"model_range_code": "q8", "model_range_description": "Q8 SUV", "series": "Q8"},
        {
            "model_range_code": "sq8",
            "model_range_description": "SQ8 SUV",
            "series": "Q8",
        },
        {
            "model_range_code": "rsq8",
            "model_range_description": "RS Q8",
            "series": "Q8",
        },
        {
            "model_range_code": "q8etron",
            "model_range_description": "Q8 e-tron",
            "series": "Q8 e-tron",
        },
        {
            "model_range_code": "q8sbetron",
            "model_range_description": "Q8 Sportback e-tron",
            "series": "Q8 e-tron",
        },
        {
            "model_range_code": "sq8etron",
            "model_range_description": "SQ8 e-tron",
            "series": "Q8 e-tron",
        },
        {
            "model_range_code": "sq8sbetron",
            "model_range_description": "SQ8 Sportback e-tron",
            "series": "Q8 e-tron",
        },
        {
            "model_range_code": "r8",
            "model_range_description": "R8 Coupé",
            "series": "R8",
        },
    ]

    with open(f"{TEST_DATA_DIR}/finance_option_for_all_models.json", "r") as file:
        list_of_models = parse_available_model_ranges_for_finance(
            json.loads(file.read())
        )
        assert expected_list_of_models == list_of_models


def test_parse_finance_options():
    expected_list_of_finance_options = [
        {"finance_code": "835457", "name": "PCP £22000 Deposit Contribution 8.9% APR"},
        {"finance_code": "834769", "name": "PCP £14000 Deposit Contribution 4.9% APR"},
        {"finance_code": "834784", "name": "Personal Contract Hire"},
        {"finance_code": "834907", "name": "Buisness Contract Hire"},
    ]

    with open(f"{TEST_DATA_DIR}/finance_options.json", "r") as file:
        list_of_finance_options = parse_finance_options(json.loads(file.read()))

    assert expected_list_of_finance_options == list_of_finance_options


def test_parse_finance_option_details():
    expected_list_of_finance_options = {
        # if there is no down_payment key in response, then it should return zero
        "down_payment": 0.0,
        "monthly_payment": "955.56",
    }

    with open(f"{TEST_DATA_DIR}/finance_options_details.json", "r") as file:
        list_of_finance_options = parse_finance_option_details(json.loads(file.read()))

        assert expected_list_of_finance_options == list_of_finance_options


def test_parse_finance_line_item():
    expected_finance_line_item = create_test_finance_line_item(
        vendor=Vendor.AUDI,
        series="etrongt",
        model_range_code="etron",
        model_range_description="ET gtron",
        model_code="F834V",
        model_description="e-tron GT",
        line_code="vorsprung",
        line_description="e-tron GT quattro Vorsprung 60 quattro",
        contract_type="PCP £22000 Deposit Contribution 8.9% APR",
        monthly_rental_glp=1012.33,
        monthly_rental_nlp=1012.33,
        market=Market.UK,
    )

    finance_option = {
        "finance_code": "835457",
        "name": "PCP £22000 Deposit Contribution 8.9% APR",
    }
    finance_option_details = {"monthly_payment": "1012.33", "down_payment": "21903.00"}
    model = {
        "series": "etrongt",
        "model_range_code": "etron",
        "model_range_description": "ET gtron",
        "model_code": "F834V",
        "model_description": "e-tron GT",
        "line_description": "e-tron GT quattro Vorsprung 60 quattro",
        "line_code": "vorsprung",
        "price": 113515,
        "year": 2024,
    }

    actual_finance_line_item = parse_finance_line_item(
        finance_option, finance_option_details, model
    )

    assert expected_finance_line_item == actual_finance_line_item


def test_parse_model_price():
    expected_model_price = 88365
    trimline = {
        "defaultConfiguredCar": {
            "prices": {
                "priceParts": [
                    {
                        "price": {
                            "value": 88365,
                            "currencyDetails": {
                                "symbol": "£",
                                "code": "GBP",
                                "__typename": "Currency",
                            },
                            "__typename": "Price",
                        },
                        "type": "financeableTotal",
                        "__typename": "FinanceableTypedPrice",
                    },
                    {
                        "price": {
                            "value": 86585,
                            "currencyDetails": {
                                "symbol": "£",
                                "code": "GBP",
                                "__typename": "Currency",
                            },
                            "__typename": "Price",
                        },
                        "type": "model",
                        "__typename": "FinanceableTypedPrice",
                    },
                    {
                        "price": {
                            "value": 0,
                            "currencyDetails": {
                                "symbol": "£",
                                "code": "GBP",
                                "__typename": "Currency",
                            },
                            "__typename": "Price",
                        },
                        "type": "nonFinanceableTotal",
                        "__typename": "NonFinanceableTypedPrice",
                    },
                    {
                        "price": {
                            "value": 950,
                            "currencyDetails": {
                                "symbol": "£",
                                "code": "GBP",
                                "__typename": "Currency",
                            },
                            "__typename": "Price",
                        },
                        "type": "options",
                        "__typename": "FinanceableTypedPrice",
                    },
                    {
                        "price": {
                            "value": 88365,
                            "currencyDetails": {
                                "symbol": "£",
                                "code": "GBP",
                                "__typename": "Currency",
                            },
                            "__typename": "Price",
                        },
                        "type": "rotr",
                        "__typename": "NonFinanceableTypedPrice",
                    },
                    {
                        "price": {
                            "value": 830,
                            "currencyDetails": {
                                "symbol": "£",
                                "code": "GBP",
                                "__typename": "Currency",
                            },
                            "__typename": "Price",
                        },
                        "type": "rotrRate",
                        "__typename": "NonFinanceableTypedPrice",
                    },
                    {
                        "price": {
                            "value": 87535,
                            "currencyDetails": {
                                "symbol": "£",
                                "code": "GBP",
                                "__typename": "Currency",
                            },
                            "__typename": "Price",
                        },
                        "type": "total",
                        "__typename": "FinanceableTypedPrice",
                    },
                    {
                        "price": {
                            "value": 647.58,
                            "currencyDetails": {
                                "symbol": "£",
                                "code": "GBP",
                                "__typename": "Currency",
                            },
                            "__typename": "Price",
                        },
                        "type": "totalRate",
                        "__typename": "NonFinanceableTypedPrice",
                    },
                ]
            }
        }
    }
    parsed_model_price = parse_model_price(trimline)
    assert expected_model_price == parsed_model_price


def test_parse_addon_options():
    trimline = {
        "name": "Black Edition 55 TFSI e quattro tiptronic",
        "engineName": "Black Edition 55 TFSI e quattro tiptronic",
        "gearType": "undefined",
        "defaultConfiguredCar": {
            "catalog": {
                "features": {
                    "data": [
                        {
                            "name": "Pure white, solid",
                            "family": {
                                "id": "color-type:uni",
                                "name": "Solid paint finishes",
                                "__typename": "CarFeatureFamily",
                            },
                            "price": {
                                "formattedValue": "0.00 GBP",
                                "currencyDetails": {
                                    "code": "GBP",
                                    "symbol": "£",
                                    "__typename": "Currency",
                                },
                                "value": 0,
                                "valueAsText": "0.00",
                                "__typename": "Price",
                            },
                            "__typename": "ConfiguredCarFeature",
                        }
                    ],
                    "__typename": "ConfiguredCarFeatures",
                },
                "__typename": "ConfiguredCarCatalog",
            },
            "__typename": "ConfiguredCar",
        },
        "__typename": "Model",
    }
    # Expected output
    expected_addon_options = {
        "option_description": "Pure white, solid",
        "option_gross_list_price": 0,
        "option_type": "color-type:uni",
    }
    parsed_addon_options = parse_addon_options(trimline)
    assert expected_addon_options == parsed_addon_options


def test_parse_pcp_finance_option_details():
    expected_list_of_finance_options = {
        "annual_mileage": "10000",
        "apr": "8.9",
        "deposit": 0.0,
        "down_payment": 0.0,
        "excess_mileage": "17.28",
        "fixed_roi": "8.86",
        "monthly_payment": "955.56",
        "option_purchase_fee": "10.00",
        "optional_final_payment": "44296.60",
        "otr": "113515",
        "sales_offer": "22000.00",
        "term_of_agreement": "48",
        "total_credit_amount": "69612.00",
        "total_deposit": "43903.00",
        "total_payable_amount": "129120.92",
        "number_of_installments": 47,
    }

    with open(f"{TEST_DATA_DIR}/finance_options_details.json", "r") as file:
        list_of_finance_options = parse_pcp_finance_option_details(
            json.loads(file.read())
        )

    assert expected_list_of_finance_options == list_of_finance_options


def test_get_number_of_installments():
    expected_number_of_installments = 47

    with open(f"{TEST_DATA_DIR}/finance_options_details.json", "r") as file:
        data = json.loads(file.read())
        actual_number_of_installments = _get_number_of_installments(data)

    assert expected_number_of_installments == actual_number_of_installments


def test_get_number_of_installments_format_issue_returns_zero():
    expected_number_of_installments = 0

    with open(f"{TEST_DATA_DIR}/finance_options_details.json", "r") as file:
        data = json.loads(file.read())
        data["Response"]["Parameters"]["Group"]["Parameter"][3]["Label"] = "abc"
        actual_number_of_installments = _get_number_of_installments(data)

    assert expected_number_of_installments == actual_number_of_installments


def test_get_number_of_installments_with_key_issue_returns_zero():
    expected_number_of_installments = 0

    with open(f"{TEST_DATA_DIR}/finance_options_details.json", "r") as file:
        data = json.loads(file.read())
        data["Response"]["Parameters"]["Group"]["Parameter"][3] = {}
        actual_number_of_installments = _get_number_of_installments(data)

    assert expected_number_of_installments == actual_number_of_installments


def test_audi_pcp_finance_line_items_contract_type_is_always_pcp():
    model = {
        "vehicle_id": "uk_aud_aa31e0a2",
        "series": "etrongt",
        "line_code": "vorsprung",
        "line_description": "e-tron GT quattro 60 quattro",
        "model_code": "F834V",
        "model_description": "e-tron GT",
        "price": 88365,
        "model_range_code": "etron",
        "model_range_description": "ET gtron",
        "year": 2024,
        "default_configured_car_options": {
            "option_description": "Glacier white, metallic",
            "option_gross_list_price": 0,
            "option_type": "color-type:metallic",
        },
    }

    expected_finance_line_item = create_test_finance_line_item(
        vehicle_id="uk_aud_aa31e0a2",
        vendor=Vendor.AUDI,
        series="etrongt",
        model_range_code="etron",
        model_range_description="ET gtron",
        model_code="F834V",
        model_description="e-tron GT",
        line_code="vorsprung",
        line_description="e-tron GT quattro 60 quattro",
        contract_type="PCP",
        monthly_rental_glp=955.56,
        monthly_rental_nlp=796.3,
        market=Market.UK,
    )

    finance_options = {
        "monthly_payment": "955.56",
        "down_payment": 0.0,
        "sales_offer": "22000.00",
        "deposit": 0.0,
        "total_deposit": "43903.00",
        "total_credit_amount": "69612.00",
        "total_payable_amount": "129120.92",
        "otr": "113515",
        "annual_mileage": "10000",
        "excess_mileage": "17.28",
        "optional_final_payment": "44296.60",
        "fixed_roi": "8.86",
        "apr": "8.9",
        "option_purchase_fee": "10.00",
        "term_of_agreement": "48",
        "number_of_installments": 47,
    }

    actual_finance_line_item = parse_pcp_finance_line_item(finance_options, model)

    assert expected_finance_line_item == actual_finance_line_item


def test_parse_finance_options_when_single_product_available_then_should_return_that_only():
    expected_list_of_finance_options = [
        {"finance_code": "835457", "name": "PCP £22000 Deposit Contribution 8.9% APR"},
    ]

    with open(f"{TEST_DATA_DIR}/finance_options_single_product.json", "r") as file:
        list_of_finance_options = parse_finance_options(json.loads(file.read()))

    assert expected_list_of_finance_options == list_of_finance_options
