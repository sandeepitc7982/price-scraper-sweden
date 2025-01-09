import json
import unittest
from pathlib import Path
from test.price_monitor.utils.test_data_builder import create_test_finance_line_item
from unittest.mock import Mock, patch

from requests import HTTPError

from src.price_monitor.finance_scraper.audi.finance_scraper_uk import (
    FinanceScraperAudiUk,
    find_available_finance_model_ranges,
)
from src.price_monitor.model.vendor import Market, Vendor

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"


class TestFinanceScraper(unittest.TestCase):
    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_available_model_ranges_for_finance"
    )
    @patch("src.price_monitor.finance_scraper.audi.finance_scraper_uk.execute_request")
    def test_find_available_models(
        self, mock_execute_request, mock_parse_available_models_for_finance
    ):
        expected_result = "I am Data"
        mock_execute_request.return_value = "available models"
        mock_session = Mock()
        mock_session.return_value = "I am Data"
        mock_parse_available_models_for_finance.return_value = "I am Data"

        actual_result = find_available_finance_model_ranges(session=mock_session)
        mock_execute_request.assert_called_with(
            "get",
            "https://fa-finance-tool.api.prod.collab.apps.one.audi/api/carline_lookup",
            mock_session,
        )
        assert actual_result == expected_result

    @patch.object(FinanceScraperAudiUk, "_scrape_finance_option_for_model")
    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.find_available_finance_model_ranges"
    )
    def test_scrape_finance_options_for_uk(
        self,
        mock_find_available_finance_model_ranges,
        mock_scrape_finance_option_for_model,
    ):
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]

        mock_find_available_finance_model_ranges.return_value = [
            {
                "model_range_code": "model_code",
                "model_range_description": "model_description",
            }
        ]
        mock_scrape_finance_option_for_model.return_value = [finance_line_item]
        mock_session = Mock()
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        actual_result = finance_scraper_audi_uk.scrape_finance_options_for_uk()

        assert actual_result == expected_result

    @patch.object(FinanceScraperAudiUk, "_scrape_finance_able_details_for_models")
    def test_scrape_finance_option_for_model(
        self, mock_scrape_finance_able_details_for_models
    ):
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]

        model = {
            "model_code": "model_code",
            "model_description": "model_description",
            "model_range_code": "model_range_code",
            "model_range_description": "model_range",
        }
        mock_scrape_finance_able_details_for_models.return_value = [finance_line_item]
        mock_session = Mock()
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        actual_result = finance_scraper_audi_uk._scrape_finance_option_for_model(model)

        assert actual_result == expected_result

    @patch.object(FinanceScraperAudiUk, "_scrape_finance_able_details_for_models")
    @patch("src.price_monitor.finance_scraper.audi.finance_scraper_uk.logger")
    def test_scrape_finance_option_for_model_calls_logger_when_it_fails(
        self, mock_logger, mock_scrape_finance_able_details_for_models
    ):
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        model = {
            "model_code": "model_code",
            "model_description": "model_description",
            "model_range_code": "model_range_code",
            "model_range_description": "model_range",
        }
        mock_scrape_finance_able_details_for_models.side_effect = HTTPError()
        mock_session = Mock()
        mock_finance_line_item_repository = Mock()
        mock_finance_line_item_repository.load_model_filter_by_model_range_description.return_value = [
            finance_line_item
        ]
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=mock_finance_line_item_repository,
            config=config,
            session=mock_session,
        )
        actual_result = finance_scraper_audi_uk._scrape_finance_option_for_model(model)

        assert actual_result == expected_result
        mock_logger.error.assert_called_with(
            "[UK] Unable to scrape for model_link {'model_code': 'model_code', 'model_description': 'model_description'"
            ", 'model_range_code': 'model_range_code', 'model_range_description': 'model_range'} , due to error: . "
            "Loading From Previous Day....."
        )
        mock_logger.info.assert_called_with("Loaded 1 for model_range_code-model_range")

    @patch.object(FinanceScraperAudiUk, "_get_available_finance_options")
    @patch.object(FinanceScraperAudiUk, "_get_alt_keys_for_model")
    @patch("src.price_monitor.finance_scraper.audi.finance_scraper_uk.execute_request")
    def test_scrape_finance_able_details_for_models(
        self,
        mock_execute_request,
        mock_get_alt_keys_for_model,
        mock_get_available_finance_options,
    ):
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        model = {
            "model_range_code": "model_range_code",
            "model_range_description": "model_range_description",
        }
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]

        mock_session = Mock()
        mock_execute_request.return_value = {
            "data": {
                "configuredCarByCarline": {
                    "carlineStructureCarline": {
                        "trimlines": [
                            {
                                "id": "trimline_performance",
                                "name": "RS 6 Avant performance",
                                "models": [
                                    {
                                        "name": "performance tiptronic",
                                        "engineName": "quattro tiptronic",
                                        "gearType": "undefined",
                                        "defaultConfiguredCar": {
                                            "id": {
                                                "country": "gb",
                                                "language": "en",
                                                "brand": "A",
                                                "salesGroup": "50894",
                                                "model": {
                                                    "year": 2024,
                                                    "code": "4A5RRA",
                                                    "version": 1,
                                                    "extensions": [],
                                                    "extensionsPR7": [],
                                                    "__typename": "ConfiguredCarModelIdentifier",
                                                },
                                                "exteriorColor": "9W9W",
                                                "interiorColor": "UB",
                                                "equipmentOptions": ["GPEGPEG"],
                                                "__typename": "ConfiguredCarIdentifier",
                                            },
                                            "prices": {
                                                "priceParts": [
                                                    {
                                                        "price": {
                                                            "value": 112045,
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
                                                        "type": "options",
                                                        "__typename": "FinanceableTypedPrice",
                                                    },
                                                    {
                                                        "price": {
                                                            "value": 115620,
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
                                                            "value": 3575,
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
                                                            "value": 112045,
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
                                                ],
                                                "__typename": "ConfiguredCarPrices",
                                            },
                                            "technicalData": {
                                                "consumptionAndEmission": {
                                                    "measurements": [
                                                        {
                                                            "fuelType": "PETROL",
                                                            "wltp": {
                                                                "consolidated": {
                                                                    "emissionCO2": {
                                                                        "combined": {
                                                                            "formattedValue": "460.3 g/mile",
                                                                            "value": 460.3,
                                                                            "__typename": "TechnicalDataFloatItem",
                                                                        },
                                                                        "__typename": "ValuesWltp",
                                                                    },
                                                                    "consumption": {
                                                                        "combined": {
                                                                            "formattedValue": "22.4 mpg",
                                                                            "value": 22.4,
                                                                            "__typename": "TechnicalDataFloatItem",
                                                                        },
                                                                        "__typename": "ValuesWltp",
                                                                    },
                                                                    "__typename": "TechnicalDataConsumptionAndEmissionValuesPerEnergyManagementWltp",
                                                                },
                                                                "__typename": "TechnicalDataConsumptionAndEmissionValuesWltp",
                                                            },
                                                            "__typename": "TechnicalDataConsumptionAndEmissionPerFuel",
                                                        }
                                                    ],
                                                    "__typename": "TechnicalDataConsumptionAndEmission",
                                                },
                                                "__typename": "ConfiguredCarTechnicalData",
                                            },
                                            "catalog": {
                                                "features": {
                                                    "data": [
                                                        {
                                                            "name": "Ascari blue, metallic",
                                                            "family": {
                                                                "id": "color-type:metallic",
                                                                "name": "Metallic paint finishes",
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
                                ],
                                "__typename": "Trimline",
                            }
                        ]
                    }
                }
            }
        }
        mock_get_alt_keys_for_model.return_value = {"4A5RRA\\1": "altKey"}
        mock_get_available_finance_options.return_value = [finance_line_item]
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        actual_result = finance_scraper_audi_uk._scrape_finance_able_details_for_models(
            model
        )

        assert actual_result == expected_result

    @patch("src.price_monitor.finance_scraper.audi.finance_scraper_uk.execute_request")
    def test_get_alt_keys_for_model(self, mock_execute_request):
        expected_result = {"model_code": "cap_code"}
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}

        mock_session = Mock()
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        model_codes = ["model_code"]
        mock_execute_request.return_value = [
            {"ModelCode": "model_code", "Capcode": "cap_code"}
        ]
        actual_result = finance_scraper_audi_uk._get_alt_keys_for_model(model_codes)

        assert actual_result == expected_result

    @patch.object(FinanceScraperAudiUk, "_get_finance_details_for_finance_option")
    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_finance_options"
    )
    @patch("src.price_monitor.finance_scraper.audi.finance_scraper_uk.execute_request")
    def test_get_available_finance_options(
        self,
        mock_get_finance_details_for_finance_option,
        mock_execute_request,
        mock_parse_finance_options,
    ):
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        finance_line_item = create_test_finance_line_item()
        expected_result = [finance_line_item]

        mock_session = Mock()
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        mock_execute_request.return_value = ["data"]
        mock_parse_finance_options.return_value = finance_line_item
        mock_get_finance_details_for_finance_option.return_value = finance_line_item
        model = {"year": 2004, "price": 3000}
        actual_result = finance_scraper_audi_uk._get_available_finance_options(
            "altKey", model
        )

        assert actual_result == expected_result

    @patch.object(FinanceScraperAudiUk, "_get_finance_line_item")
    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_finance_option_details"
    )
    @patch("src.price_monitor.finance_scraper.audi.finance_scraper_uk.execute_request")
    def test_get_finance_details_for_finance_option(
        self,
        mock_get_finance_line_item,
        mock_execute_request,
        mock_parse_finance_option_details,
    ):
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        finance_line_item = create_test_finance_line_item()
        expected_result = finance_line_item

        mock_session = Mock()
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        mock_execute_request.return_value = ["data"]
        mock_parse_finance_option_details.return_value = finance_line_item
        mock_get_finance_line_item.return_value = finance_line_item
        finance_option = {
            "finance_code": "835457",
            "name": "PCP £22000 Deposit Contribution 8.9% APR",
        }
        alt_key = "AUEG00   4SE A4"
        model = {
            "model_code": "etrongt",
            "model_description": "e-tron GT",
            "line_description": "e-tron GT quattro 60 quattro",
            "line_code": "default",
            "price": 88365,
            "year": 2024,
        }

        actual_result = finance_scraper_audi_uk._get_finance_details_for_finance_option(
            finance_option=finance_option, alt_key=alt_key, model=model
        )

        assert actual_result == expected_result

    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_pcp_finance_line_item"
    )
    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_pcp_finance_option_details"
    )
    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_finance_line_item"
    )
    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_finance_option_details"
    )
    @patch("src.price_monitor.finance_scraper.audi.finance_scraper_uk.execute_request")
    def test_get_finance_line_item_when_contract_type_is_pcp(
        self,
        mock_execute_request,
        mock_parse_finance_option_details,
        mock_parse_finance_line_item,
        mock_parse_pcp_finance_option_details,
        mock_parse_pcp_finance_line_item,
    ):
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        finance_line_item = create_test_finance_line_item()
        expected_result = finance_line_item

        mock_session = Mock()
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        mock_execute_request.return_value = {
            "Response": {
                "Calculation": {"InstallmentGrossAmount": 123},
                "Parameters": {"23"},
            }
        }
        mock_parse_finance_option_details.return_value = finance_line_item
        mock_parse_finance_line_item.return_value = finance_line_item
        finance_option = {
            "finance_code": "835457",
            "name": "PCP £22000 Deposit Contribution 8.9% APR",
        }
        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115 Safari/537.36 ",
        }
        model = {
            "model_code": "etrongt",
            "model_description": "e-tron GT",
            "line_description": "e-tron GT quattro 60 quattro",
            "line_code": "default",
            "price": 88365,
            "year": 2024,
        }
        payload = {
            "Request": {
                "@Domain": "AUDI.UK.CRS",
                "@Name": "Defaults",
                "Product": {"@ID": "835457", "Parameter": []},
                "Vehicle": {
                    "AltKey": "AUEG00   4SE A4",
                    "PriceTotal": 88365,
                    "Year": 2024,
                },
            }
        }
        url = "url"
        mock_parse_pcp_finance_line_item.return_value = create_test_finance_line_item()

        actual_result = finance_scraper_audi_uk._get_finance_line_item(
            finance_option, headers, model, payload, url
        )
        mock_parse_pcp_finance_option_details.assert_called_with(
            {
                "Response": {
                    "Calculation": {"InstallmentGrossAmount": 123},
                    "Parameters": {"23"},
                }
            }
        )

        assert actual_result == expected_result

    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_pcp_finance_line_item"
    )
    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_pcp_finance_option_details"
    )
    @patch("src.price_monitor.finance_scraper.audi.finance_scraper_uk.execute_request")
    def test_get_pcp_finance_line_item(
        self,
        mock_execute_request,
        mock_parse_finance_option_details,
        mock_parse_finance_line_item,
    ):
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        finance_line_item = create_test_finance_line_item()
        expected_result = finance_line_item

        mock_session = Mock()
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        mock_execute_request.return_value = ["data"]
        mock_parse_finance_option_details.return_value = finance_line_item
        mock_parse_finance_line_item.return_value = finance_line_item
        finance_option = {
            "finance_code": "835457",
            "name": "PCP £22000 Deposit Contribution 8.9% APR",
        }
        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115 Safari/537.36 ",
        }
        model = {
            "model_code": "etrongt",
            "model_description": "e-tron GT",
            "line_description": "e-tron GT quattro 60 quattro",
            "line_code": "default",
            "price": 88365,
            "year": 2024,
        }
        payload = {
            "Request": {
                "@Domain": "AUDI.UK.CRS",
                "@Name": "Defaults",
                "Product": {"@ID": "835457", "Parameter": []},
                "Vehicle": {
                    "AltKey": "AUEG00   4SE A4",
                    "PriceTotal": 88365,
                    "Year": 2024,
                },
            }
        }
        url = "url"
        actual_result = finance_scraper_audi_uk._get_finance_line_item(
            finance_option, headers, model, payload, url
        )

        assert actual_result == expected_result

    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_pcp_finance_line_item"
    )
    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_pcp_finance_option_details"
    )
    @patch("src.price_monitor.finance_scraper.audi.finance_scraper_uk.execute_request")
    def test_get_pcp_finance_line_item_with_826999_as_finance_code(
        self,
        mock_execute_request,
        mock_parse_finance_option_details,
        mock_parse_finance_line_item,
    ):
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        finance_line_item = create_test_finance_line_item()
        expected_result = finance_line_item

        mock_session = Mock()
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        mock_execute_request.return_value = ["data"]
        mock_parse_finance_option_details.return_value = finance_line_item
        mock_parse_finance_line_item.return_value = finance_line_item
        finance_option = {
            "finance_code": "826999",
            "name": "PCP £22000 Deposit Contribution 8.9% APR",
        }
        # finance_option_details = {
        #     "monthly_payment": "647.58",
        #     "down_payment": "16873.00",
        # }
        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115 Safari/537.36 ",
        }
        model = {
            "model_code": "etrongt",
            "model_description": "e-tron GT",
            "line_description": "e-tron GT quattro 60 quattro",
            "line_code": "default",
            "price": 88365,
            "year": 2024,
        }
        payload = {
            "Request": {
                "@Domain": "AUDI.UK.CRS",
                "@Name": "Defaults",
                "Product": {"@ID": "835457", "Parameter": []},
                "Vehicle": {
                    "AltKey": "AUEG00   4SE A4",
                    "PriceTotal": 88365,
                    "Year": 2024,
                },
            }
        }
        url = "url"
        actual_result = finance_scraper_audi_uk._get_finance_line_item(
            finance_option, headers, model, payload, url
        )

        assert actual_result == expected_result

    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_finance_line_item"
    )
    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_finance_option_details"
    )
    @patch("src.price_monitor.finance_scraper.audi.finance_scraper_uk.execute_request")
    def test_get_finance_line_item_when_contract_type_is_personal_contract_hire(
        self,
        mock_execute_request,
        mock_parse_finance_option_details,
        mock_parse_finance_line_item,
    ):
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        finance_line_item = create_test_finance_line_item()
        expected_result = finance_line_item

        mock_session = Mock()
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        mock_execute_request.return_value = ["data"]
        mock_parse_finance_option_details.return_value = finance_line_item
        mock_parse_finance_line_item.return_value = finance_line_item
        finance_option = {
            "finance_code": "834784",
            "name": "Personal Contract Hire",
        }

        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115 Safari/537.36 ",
        }
        model = {
            "model_code": "etrongt",
            "model_description": "e-tron GT",
            "line_description": "e-tron GT quattro 60 quattro",
            "line_code": "default",
            "price": 88365,
            "year": 2024,
        }
        payload = {
            "Request": {
                "@Domain": "AUDI.UK.CRS",
                "@Name": "Defaults",
                "Product": {"@ID": "835457", "Parameter": []},
                "Vehicle": {
                    "AltKey": "AUEG00   4SE A4",
                    "PriceTotal": 88365,
                    "Year": 2024,
                },
            }
        }
        url = "url"
        actual_result = finance_scraper_audi_uk._get_finance_line_item(
            finance_option, headers, model, payload, url
        )

        assert actual_result == expected_result

    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_finance_line_item"
    )
    @patch(
        "src.price_monitor.finance_scraper.audi.finance_scraper_uk.parse_finance_option_details"
    )
    @patch("src.price_monitor.finance_scraper.audi.finance_scraper_uk.execute_request")
    def test_get_finance_line_item_with_826999_as_finance_code(
        self,
        mock_execute_request,
        mock_parse_finance_option_details,
        mock_parse_finance_line_item,
    ):
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        finance_line_item = create_test_finance_line_item()
        expected_result = finance_line_item

        mock_session = Mock()
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        mock_execute_request.return_value = ["data"]
        mock_parse_finance_option_details.return_value = finance_line_item
        mock_parse_finance_line_item.return_value = finance_line_item
        finance_option = {
            "finance_code": "834784",
            "name": "Personal Contract Hire",
        }

        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115 Safari/537.36 ",
        }
        model = {
            "model_code": "etrongt",
            "model_description": "e-tron GT",
            "line_description": "e-tron GT quattro 60 quattro",
            "line_code": "default",
            "price": 88365,
            "year": 2024,
        }
        payload = {
            "Request": {
                "@Domain": "AUDI.UK.CRS",
                "@Name": "Defaults",
                "Product": {"@ID": "835457", "Parameter": []},
                "Vehicle": {
                    "AltKey": "AUEG00   4SE A4",
                    "PriceTotal": 88365,
                    "Year": 2024,
                },
            }
        }
        url = "url"
        actual_result = finance_scraper_audi_uk._get_finance_line_item(
            finance_option, headers, model, payload, url
        )

        assert actual_result == expected_result

    @patch("src.price_monitor.finance_scraper.audi.finance_scraper_uk.execute_request")
    def test__get_finance_line_item_for_pcp_financeoption_have_pcp_contract_type(
        self, mock_execute_request
    ):
        config = {"scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}
        mock_session = Mock()
        finance_scraper_audi_uk = FinanceScraperAudiUk(
            finance_line_item_repository=Mock(), config=config, session=mock_session
        )
        finance_option = {
            "finance_code": "826999",
            "name": "PCP £22000 Deposit Contribution 8.9% APR",
        }
        with open(f"{TEST_DATA_DIR}/finance_options_details.json", "r") as file:
            data = json.loads(file.read())
        mock_execute_request.return_value = data

        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115 Safari/537.36 ",
        }
        model = {
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
        payload = {
            "Request": {
                "@Domain": "AUDI.UK.CRS",
                "@Name": "Defaults",
                "Product": {"@ID": "835457", "Parameter": []},
                "Vehicle": {
                    "AltKey": "AUEG00   4SE A4",
                    "PriceTotal": 88365,
                    "Year": 2024,
                },
            }
        }
        url = "url"
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

        actual_result = finance_scraper_audi_uk._get_finance_line_item(
            finance_option, headers, model, payload, url
        )

        assert actual_result == expected_finance_line_item
