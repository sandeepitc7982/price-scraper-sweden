import json
import unittest
from pathlib import Path
from test.price_monitor.utils.test_data_builder import (
    create_test_finance_line_item,
    create_test_line_item,
)
from unittest.mock import Mock, patch

from requests import HTTPError

from src.price_monitor.finance_scraper.bmw.constants import BMW_UK_FINANCE_OPTION_URL
from src.price_monitor.finance_scraper.bmw.finance_scraper import (
    FinanceScraperBMWUk,
    get_lowest_price_metallic_paint,
    get_metallic_paints,
    parse_metallic_paint,
    update_selected_options_with_metallic_paint,
)
from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.vendor import Currency, Market, Vendor
from src.price_monitor.utils.clock import (
    today_dashed_str,
    yesterday_dashed_str_with_key,
)

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"


class TestFinanceScraper(unittest.TestCase):
    @patch("src.price_monitor.finance_scraper.bmw.finance_scraper.get_updated_token")
    @patch.object(FinanceScraperBMWUk, "get_finance_option_for_line")
    def test_scrape_finance_options_for_uk(
        self, mock_get_finance_option_for_line, mock_get_updated_token
    ):
        finance_line_item = create_test_finance_line_item(
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

        parsed_line_items = [
            create_test_line_item(
                recorded_at=today_dashed_str(),
                vendor=Vendor.BMW,
                market=Market.UK,
            ),
        ]
        config = {"scraper": {"enabled": {Vendor.BMW: [Market.UK]}}}
        mock_get_updated_token.return_value = "token123"

        mock_session = Mock()

        bmw_finance_scraper = FinanceScraperBMWUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        mock_get_finance_option_for_line.return_value = [finance_line_item]

        actual_finance_line_items = bmw_finance_scraper.scrape_finance_options_for_uk(
            parsed_line_items, "model_matrix"
        )
        mock_get_finance_option_for_line.assert_called_with(
            parsed_line_items[0],
            "model_matrix",
        )
        assert actual_finance_line_items[0].asdict() == finance_line_item.asdict()

    @patch(
        "src.price_monitor.finance_scraper.bmw.finance_scraper.get_lowest_price_metallic_paint"
    )
    @patch("src.price_monitor.finance_scraper.bmw.finance_scraper.get_metallic_paints")
    @patch("src.price_monitor.finance_scraper.bmw.finance_scraper.parse_is_volt_48")
    @patch(
        "src.price_monitor.finance_scraper.bmw.finance_scraper.get_configuration_state_and_is_volt_48"
    )
    @patch.object(FinanceScraperBMWUk, "get_finance_line_item_for_finance_option")
    @patch("src.price_monitor.finance_scraper.bmw.finance_scraper.execute_request")
    def test_get_finance_option_for_line(
        self,
        mock_execute_request,
        mock_get_finance_line_item_for_finance_option,
        mock_get_configuration_state_and_is_volt_48,
        mock_parse_is_volt_48,
        mock_get_metallic_paints,
        mock_get_lowest_price_metallic_paint,
    ):
        expected_finance_line_item = create_test_finance_line_item()
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
        mock_get_configuration_state_and_is_volt_48.return_value = "testing"
        mock_parse_is_volt_48.return_value = False
        mock_execute_request.return_value = {
            "financeProductList": [{"productId": "PCP"}]
        }
        mock_get_finance_line_item_for_finance_option.return_value = (
            expected_finance_line_item
        )
        metallic_paints = [
            {
                "option_type": "paint",
                "paint_code": "P0C6R",
                "paint_description": "BMW Individual Frozen Portimao Blue ",
            },
            {
                "option_type": "paint",
                "paint_code": "P0C5A",
                "paint_description": "BMW Individual Frozen Pure Grey",
            },
            {
                "option_type": "paint",
                "paint_code": "P0C4W",
                "paint_description": "Skyscraper Grey ",
            },
            {
                "option_type": "paint",
                "paint_code": "P0C56",
                "paint_description": "Thundernight",
            },
            {
                "option_type": "paint",
                "paint_code": "P0475",
                "paint_description": "Black Sapphire ",
            },
            {
                "option_type": "paint",
                "paint_code": "P0C3N",
                "paint_description": "Storm Bay",
            },
            {
                "option_type": "paint",
                "paint_code": "P0C31",
                "paint_description": "Portimao Blue",
            },
        ]
        non_metallic_paints = [
            {
                "option_type": "paint",
                "paint_code": "P0300",
                "paint_description": "Alpine White",
            }
        ]
        mock_get_metallic_paints.return_value = [metallic_paints, non_metallic_paints]

        mock_get_lowest_price_metallic_paint.return_value = {
            "option_type": "paint",
            "paint_code": "P0C4W",
            "paint_description": "Skyscraper Grey ",
            "paint_price": 650.0,
        }
        config = {"scraper": {"enabled": {Vendor.BMW: [Market.UK]}}}
        mock_session = Mock()
        bmw_finance_scraper = FinanceScraperBMWUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )

        setattr(bmw_finance_scraper, "token", "token123")
        setattr(bmw_finance_scraper, "IX_MODELS", [])

        with open(f"{TEST_DATA_DIR}/model_matrix_series_z.json", "r") as file:
            model_matrix = json.load(file)
            parsed_finance_line_item = bmw_finance_scraper.get_finance_option_for_line(
                line_item, model_matrix
            )

        mock_execute_request.assert_called_with(
            "post",
            BMW_UK_FINANCE_OPTION_URL,
            headers={"content-type": "application/json"},
            body={
                "settings": {
                    "application": "CONX",
                    "taxDate": "2022-10-31",
                    "effectDate": "2023-01-02",
                    "orderDate": "2022-10-31",
                },
                "vehicle": {
                    "modelCode": "HF51",
                    "isVolt48Variant": False,
                    "selectedEquipments": ["P0C4W"],
                },
            },
        )
        mock_get_finance_line_item_for_finance_option.assert_called_with(
            line_item,
            {
                "settings": {
                    "application": "CONX",
                    "taxDate": "2022-10-31",
                    "effectDate": "2023-01-02",
                    "orderDate": "2022-10-31",
                },
                "vehicle": {
                    "modelCode": "HF51",
                    "isVolt48Variant": False,
                    "selectedEquipments": ["P0C4W"],
                },
            },
            "PCP",
            {
                "option_type": "paint",
                "paint_code": "P0C4W",
                "paint_description": "Skyscraper Grey ",
                "paint_price": 650.0,
            },
        )

        assert (
            expected_finance_line_item.asdict() == parsed_finance_line_item[0].asdict()
        )

    @patch(
        "src.price_monitor.finance_scraper.bmw.finance_scraper.get_lowest_price_metallic_paint"
    )
    @patch("src.price_monitor.finance_scraper.bmw.finance_scraper.get_metallic_paints")
    @patch("src.price_monitor.finance_scraper.bmw.finance_scraper.parse_is_volt_48")
    @patch(
        "src.price_monitor.finance_scraper.bmw.finance_scraper.get_configuration_state_and_is_volt_48"
    )
    @patch.object(FinanceScraperBMWUk, "get_finance_line_item_for_finance_option")
    @patch("src.price_monitor.finance_scraper.bmw.finance_scraper.execute_request")
    def test_get_finance_option_for_line_when_500_error_occurs(
        self,
        mock_execute_request,
        mock_get_finance_line_item_for_finance_option,
        mock_get_configuration_state_and_is_volt_48,
        mock_parse_is_volt_48,
        mock_get_metallic_paints,
        mock_get_lowest_price_metallic_paint,
    ):
        expected_finance_line_item = create_test_finance_line_item(Vendor.BMW)
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
        mock_finance_line_item_repository = Mock()
        mock_finance_line_item_repository.load_model_filter_by_line_code.return_value = [
            expected_finance_line_item
        ]
        mock_get_configuration_state_and_is_volt_48.return_value = "testing"
        mock_parse_is_volt_48.return_value = False
        mock_execute_request.return_value = HTTPError()
        config = {"scraper": {"enabled": {Vendor.BMW: [Market.UK]}}}
        mock_session = Mock()
        bmw_finance_scraper = FinanceScraperBMWUk(
            finance_line_item_repository=mock_finance_line_item_repository,
            config=config,
            session=mock_session,
        )
        setattr(bmw_finance_scraper, "token", "token123")
        setattr(bmw_finance_scraper, "IX_MODELS", [])

        metallic_paints = [
            {
                "option_type": "paint",
                "paint_code": "P0C6R",
                "paint_description": "BMW Individual Frozen Portimao Blue ",
            },
            {
                "option_type": "paint",
                "paint_code": "P0C5A",
                "paint_description": "BMW Individual Frozen Pure Grey",
            },
            {
                "option_type": "paint",
                "paint_code": "P0C4W",
                "paint_description": "Skyscraper Grey ",
            },
            {
                "option_type": "paint",
                "paint_code": "P0C56",
                "paint_description": "Thundernight",
            },
            {
                "option_type": "paint",
                "paint_code": "P0475",
                "paint_description": "Black Sapphire ",
            },
            {
                "option_type": "paint",
                "paint_code": "P0C3N",
                "paint_description": "Storm Bay",
            },
            {
                "option_type": "paint",
                "paint_code": "P0C31",
                "paint_description": "Portimao Blue",
            },
        ]
        non_metallic_paints = [
            {
                "option_type": "paint",
                "paint_code": "P0300",
                "paint_description": "Alpine White",
            }
        ]
        mock_get_metallic_paints.return_value = [metallic_paints, non_metallic_paints]

        mock_get_lowest_price_metallic_paint.return_value = {
            "option_type": "paint",
            "paint_code": "P0C4W",
            "paint_description": "Skyscraper Grey ",
            "paint_price": 650.0,
        }

        with open(f"{TEST_DATA_DIR}/model_matrix_series_z.json", "r") as file:
            model_matrix = json.load(file)
            parsed_finance_line_item = bmw_finance_scraper.get_finance_option_for_line(
                line_item, model_matrix
            )

        mock_execute_request.assert_called_with(
            "post",
            BMW_UK_FINANCE_OPTION_URL,
            headers={"content-type": "application/json"},
            body={
                "settings": {
                    "application": "CONX",
                    "taxDate": "2022-10-31",
                    "effectDate": "2023-01-02",
                    "orderDate": "2022-10-31",
                },
                "vehicle": {
                    "modelCode": "HF51",
                    "isVolt48Variant": False,
                    "selectedEquipments": ["P0C4W"],
                },
            },
        )
        mock_finance_line_item_repository.load_model_filter_by_line_code.assert_called_with(
            yesterday_dashed_str_with_key(),
            Market.UK,
            Vendor.BMW,
            "Z",
            "G29",
            "HF51",
            "M_PERFORMANCE_LINE",
        )

        assert [expected_finance_line_item] == parsed_finance_line_item

    @patch("src.price_monitor.finance_scraper.bmw.finance_scraper.execute_request")
    def test_get_finance_line_item_for_finance_option(self, mock_execute_request):
        expected_finance_line_item = create_test_finance_line_item(
            vendor=Vendor.BMW,
            series="Z",
            model_range_code="G29",
            model_range_description="BMW Z4",
            model_code="HF51",
            model_description="BMW Z4 M40i - automatic",
            line_code="M_PERFORMANCE_LINE",
            line_description="M_PERFORMANCE_LINE",
            contract_type="CONTRACT_HIRE",
            monthly_rental_nlp=416.67,
            monthly_rental_glp=500.0,
            market=Market.UK,
        )
        mock_execute_request.return_value = {
            "financeProductList": [
                {
                    "parameters": [
                        {"id": "installment/grossAmount", "value": 500},
                    ]
                }
            ]
        }

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
        payload = {"settings": {"application": "CONX"}}
        config = {"scraper": {"enabled": {Vendor.BMW: [Market.UK]}}}
        mock_session = Mock()
        bmw_finance_scraper = FinanceScraperBMWUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        setattr(bmw_finance_scraper, "IX_MODELS", [])

        lowest_price_metallic_paint = {
            "option_type": "paint",
            "paint_code": "P0C4W",
            "paint_description": "Skyscraper Grey ",
            "paint_price": 650.0,
        }

        parsed_finance_line_item = (
            bmw_finance_scraper.get_finance_line_item_for_finance_option(
                line_item, payload, "CONTRACT_HIRE", lowest_price_metallic_paint
            )
        )

        mock_execute_request.assert_called_with(
            "post",
            BMW_UK_FINANCE_OPTION_URL,
            headers={"content-type": "application/json"},
            body={
                "settings": {"application": "CONX"},
                "financeProduct": {
                    "productId": "CONTRACT_HIRE",
                    "parameters": [
                        {"id": "annualMileage", "value": 10000},
                        {"id": "downPaymentAmount/grossAmount", "value": 4999},
                        {"id": "term", "value": 48},
                    ],
                },
            },
        )
        assert expected_finance_line_item == parsed_finance_line_item

    @patch("src.price_monitor.finance_scraper.bmw.finance_scraper.execute_request")
    def test_get_finance_line_item_for_finance_option_for_pcp(
        self, mock_execute_request
    ):
        expected_finance_line_item = FinanceLineItem(
            vendor=Vendor.BMW,
            series="Z",
            model_range_code="G29",
            model_range_description="BMW Z4",
            model_code="HF51",
            model_description="BMW Z4 M40i - automatic",
            line_code="M_PERFORMANCE_LINE",
            line_description="M_PERFORMANCE_LINE",
            contract_type="PCP",
            monthly_rental_nlp=416.67,
            monthly_rental_glp=500.0,
            market=Market.UK,
            term_of_agreement=30,
            number_of_installments=47,
            deposit=4500,
            total_deposit=4500,
            total_credit_amount=4500,
            total_payable_amount=600,
            otr=500,
            annual_mileage=10000,
            excess_mileage=2500,
            optional_final_payment=1500,
            apr=30,
            fixed_roi=30,
            sales_offer=1500,
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            currency=Currency[Market.UK].value,
            option_gross_list_price=650.0,
            option_description="Skyscraper Grey ",
            option_type="paint",
        )
        mock_execute_request.return_value = {
            "financeProductList": [
                {
                    "parameters": [
                        {"id": "installment/grossAmount", "value": 500},
                        {"id": "term", "value": 30},
                        {"id": "installmentPeriodCount", "value": 47},
                        {"id": "totalDeposit/grossAmount", "value": 4500},
                        {"id": "downPaymentAmount/grossAmount", "value": 4500},
                        {"id": "financeAmount/grossAmount", "value": 4500},
                        {"id": "sumOfAllPayments/grossAmount", "value": 600},
                        {"id": "calculatedVehicleAmount/grossAmount", "value": 500},
                        {"id": "annualMileage", "value": 10000},
                        {
                            "id": "excessContractualMileageAmount/grossAmount",
                            "value": 2500,
                        },
                        {"id": "residualValueAmount/grossAmount", "value": 1500},
                        {"id": "interestEffective", "value": 0.3},
                        {"id": "depositContribution/grossAmount", "value": 1500},
                    ]
                }
            ]
        }

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
        payload = {"settings": {"application": "CONX"}}
        config = {"scraper": {"enabled": {Vendor.BMW: [Market.UK]}}}
        mock_session = Mock()
        bmw_finance_scraper = FinanceScraperBMWUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        setattr(bmw_finance_scraper, "IX_MODELS", [])

        lowest_price_metallic_paint = {
            "option_type": "paint",
            "paint_code": "P0C4W",
            "paint_description": "Skyscraper Grey ",
            "paint_price": 650.0,
        }

        parsed_finance_line_item = (
            bmw_finance_scraper.get_finance_line_item_for_finance_option(
                line_item, payload, "PCP", lowest_price_metallic_paint
            )
        )

        mock_execute_request.assert_called_with(
            "post",
            BMW_UK_FINANCE_OPTION_URL,
            headers={"content-type": "application/json"},
            body={
                "settings": {"application": "CONX"},
                "financeProduct": {
                    "productId": "PCP",
                    "parameters": [
                        {"id": "annualMileage", "value": 10000},
                        {"id": "downPaymentAmount/grossAmount", "value": 4999},
                        {"id": "term", "value": 48},
                    ],
                },
            },
        )
        assert expected_finance_line_item == parsed_finance_line_item

    @patch(
        "src.price_monitor.finance_scraper.bmw.finance_scraper.get_available_options"
    )
    def test_get_metallic_paints(self, mock_get_available_options):
        # Sample data to be returned by get_available_options
        mock_get_available_options.return_value = {
            "A123": {
                "familyCode": "MET",
                "optionType": "Color",
                "phrases": {"longDescription": "Metallic Silver"},
            },
            "B456": {
                "familyCode": "UNI",
                "optionType": "Color",
                "phrases": {"longDescription": "Non-Metallic Red"},
            },
            "C789": {
                "familyCode": "MET",
                "optionType": "Color",
                "phrases": {"longDescription": "Metallic Blue"},
            },
        }

        # Parameters for the function call
        model_matrix = {}
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
        tax_date = "2023-01-01"
        effect_date = "2023-01-01"
        market = "UK"
        session = "session"
        headers = {}
        ix_models = []

        # Expected output
        expected_metallic_paints = [
            {
                "option_type": "Color",
                "paint_code": "A123",
                "paint_description": "Metallic Silver",
            },
            {
                "option_type": "Color",
                "paint_code": "C789",
                "paint_description": "Metallic Blue",
            },
        ]

        expected_non_metallic_paints = [
            {
                "option_type": "Color",
                "paint_code": "B456",
                "paint_description": "Non-Metallic Red",
            }
        ]

        metallic_paints, non_metallic_paints = get_metallic_paints(
            model_matrix,
            line_item,
            tax_date,
            effect_date,
            market,
            session,
            headers,
            ix_models,
        )

        self.assertEqual(metallic_paints, expected_metallic_paints)
        self.assertEqual(non_metallic_paints, expected_non_metallic_paints)

    @patch("src.price_monitor.finance_scraper.bmw.finance_scraper.get_options_prices")
    @patch("src.price_monitor.finance_scraper.bmw.finance_scraper.parse_metallic_paint")
    def test_get_lowest_price_metallic_paint(
        self, mock_parse_metallic_paint, mock_get_options_prices
    ):
        # Sample data
        metallic_paints = [
            {"paint_code": "P001", "paint_name": "Red Metallic"},
            {"paint_code": "P002", "paint_name": "Blue Metallic"},
            {"paint_code": "P003", "paint_name": "Green Metallic"},
        ]

        # Mock return value of get_options_prices and parse_metallic_paint
        mock_get_options_prices.return_value = {
            "availableOptions": [
                {"paint_code": "P001", "paint_price": 1000},
                {"paint_code": "P002", "paint_price": 800},
                {"paint_code": "P003", "paint_price": 1200},
            ]
        }
        mock_parse_metallic_paint.return_value = [
            {"paint_code": "P001", "paint_price": 1000},
            {"paint_code": "P002", "paint_price": 800},
            {"paint_code": "P003", "paint_price": 1200},
        ]

        # Other necessary arguments
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
        tax_date = "2024-08-27"
        effect_date = "2024-08-27"
        market = "UK"
        session = "session"
        headers = {}
        selected_line_option_codes = []
        is_volt_48_variant = True
        ix_models = []

        result = get_lowest_price_metallic_paint(
            metallic_paints,
            line_item,
            tax_date,
            effect_date,
            market,
            session,
            headers,
            selected_line_option_codes,
            is_volt_48_variant,
            ix_models,
        )

        expected_result = {
            "paint_code": "P002",
            "paint_name": "Blue Metallic",
            "paint_price": 800,
        }

        self.assertEqual(result, expected_result)
        mock_get_options_prices.assert_called_once()
        mock_parse_metallic_paint.assert_called_once_with(
            mock_get_options_prices.return_value["availableOptions"],
            ["P001", "P002", "P003"],
        )

    def test_parse_metallic_paint(self):
        # Sample response and metallic_paints input
        available_options = [
            {"optionCode": "P001", "grossListPrice": 1000},
            {"optionCode": "P002", "grossListPrice": 1500},
            {"optionCode": "P003", "grossListPrice": 2000},
        ]
        metallic_paints = ["P001", "P003", "P004"]

        # Expected output
        expected_output = [
            {"paint_code": "P001", "paint_price": 1000},
            {"paint_code": "P003", "paint_price": 2000},
        ]

        result = parse_metallic_paint(available_options, metallic_paints)

        self.assertEqual(result, expected_output)

    def test_update_selected_options_with_metallic_paint(self):
        selected_line_option_codes = ["N001", "P001", "X001"]
        non_metallic_paints = [
            {"paint_code": "P001", "price": 100},
            {"paint_code": "P002", "price": 150},
        ]
        metallic_paints = [
            {"paint_code": "M001", "price": 200},
            {"paint_code": "M002", "price": 400},
        ]
        lowest_price_metallic_paint = {"paint_code": "M001", "price": 200}

        # Expected output after replacing "P001" with "M001"
        expected_result = ["M001", "N001", "X001"]

        result = update_selected_options_with_metallic_paint(
            selected_line_option_codes,
            metallic_paints,
            non_metallic_paints,
            lowest_price_metallic_paint,
        )

        self.assertEqual(result, expected_result)

    def test_update_selected_options_with_metallic_paint_where_standard_option_is_metallic_paint(
        self,
    ):
        selected_line_option_codes = ["N001", "M002", "X001"]
        non_metallic_paints = [
            {"paint_code": "P001", "price": 100},
        ]
        metallic_paints = [
            {"paint_code": "M001", "price": 200},
            {"paint_code": "M002", "price": 400},
        ]
        lowest_price_metallic_paint = {"paint_code": "M001", "price": 200}

        # Expected output after replacing "M002" with "M001"
        expected_result = ["M001", "N001", "X001"]

        result = update_selected_options_with_metallic_paint(
            selected_line_option_codes,
            metallic_paints,
            non_metallic_paints,
            lowest_price_metallic_paint,
        )

        self.assertEqual(result, expected_result)
