import unittest
from test.price_monitor.utils.test_data_builder import (
    create_test_line_item,
    create_test_line_item_option_code,
)
from unittest.mock import Mock, patch

from requests import HTTPError

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.price_scraper.bmw.constants import API_KEY_URL, X_API_KEY
from src.price_monitor.price_scraper.bmw.scraper import (
    BMWScraper,
    get_configuration_state_and_is_volt_48,
    get_ix_models,
    get_model_matrix,
    get_updated_token,
)
from src.price_monitor.price_scraper.constants import NOT_AVAILABLE
from src.price_monitor.utils.clock import (
    today_dashed_str,
    yesterday_dashed_str_with_key,
)


class TestBMWScraper(unittest.TestCase):
    scraper_config = {
        "scraper": {"enabled": {Vendor.BMW: [Market.DE]}},
    }

    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    @patch("src.price_monitor.price_scraper.bmw.scraper.parse_api_token")
    def test_get_updated_token_when_scraping_done_then_updated_token_return(
        self, mock_parse_api_token, mock_execute_request
    ):
        mock_execute_request.return_value = "ACCESS_TOKEN_TEXT"
        mock_parse_api_token.return_value = "ACCESS_TOKEN"

        result = get_updated_token()

        mock_execute_request.assert_called_with(
            "get",
            API_KEY_URL,
            response_format="text",
        )
        mock_parse_api_token.assert_called_with("ACCESS_TOKEN_TEXT")
        assert result == "ACCESS_TOKEN"

    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    @patch("src.price_monitor.price_scraper.bmw.scraper.parse_api_token")
    def test_get_updated_token_when_scraping_fail_then_return_constants(
        self, mock_parse_api_token, mock_execute_request
    ):
        mock_execute_request.return_value = "ACCESS_TOKEN_TEXT"
        mock_parse_api_token.side_effect = HTTPError()

        result = get_updated_token()

        mock_execute_request.assert_called_with(
            "get",
            API_KEY_URL,
            response_format="text",
        )
        mock_parse_api_token.assert_called_with("ACCESS_TOKEN_TEXT")
        assert NOT_AVAILABLE == result

    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    def test_get_model_matrix_when_api_success_then_return_json_object(
        self, mock_execute_request
    ):
        expected_data = Mock("I am data")
        mock_session = Mock()

        mock_execute_request.return_value = expected_data
        headers = {"Content-Type": "application/json", X_API_KEY: "token_123"}

        result = get_model_matrix(Market.DE, mock_session, headers)

        mock_execute_request.assert_called_with(
            "get",
            url=f"https://prod.ucp.bmw.cloud/model-matrices/vehicle-trees/connext-bmw/sources/pcaso/brands/bmwCar/countries/de/effect-dates/{today_dashed_str()}/order-dates/{today_dashed_str()}?closest-fallback=true",
            session=mock_session,
            headers={"Content-Type": "application/json", X_API_KEY: "token_123"},
        )
        assert expected_data == result

    @patch.object(BMWScraper, "_add_available_options_for_line")
    @patch("src.price_monitor.price_scraper.bmw.scraper._get_available_language")
    @patch(
        "src.price_monitor.price_scraper.bmw.scraper.parse_model_matrix_to_line_items"
    )
    @patch("src.price_monitor.price_scraper.bmw.scraper.get_model_matrix")
    def test_scrape_models_for_market_when_api_is_successful_then_calls_add_available_options_for_line(
        self,
        mock_get_model_matrix,
        mock_parse_model_matrix_to_line_items,
        mock__get_available_language,
        mock__add_available_options_for_line,
    ):
        expected_line_item = create_test_line_item(line_description="bmw_line_item")
        expected_data = [expected_line_item]
        mock_parse_model_matrix_to_line_items.return_value = expected_data
        mock_get_model_matrix.return_value = {"key": "testing"}
        mock__get_available_language.return_value = "de"
        mock__add_available_options_for_line.return_value = expected_line_item

        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        setattr(bmw_scraper, "finance_option_response", [])
        result = bmw_scraper._scrape_models_for_market(Market.DE)

        assert mock__add_available_options_for_line.call_count == 1
        assert len(result) == 1
        assert result == expected_data

    @patch.object(BMWScraper, "_add_available_options_for_line")
    @patch("src.price_monitor.price_scraper.bmw.scraper._get_available_language")
    @patch(
        "src.price_monitor.price_scraper.bmw.scraper.parse_model_matrix_to_line_items"
    )
    @patch("src.price_monitor.price_scraper.bmw.scraper.get_model_matrix")
    def test_scrape_models_for_market_when_add_available_options_for_line_throws_an_http_error_then_fetches_yesterdays_data(
        self,
        mock_get_model_matrix,
        mock_parse_model_matrix_to_line_items,
        mock__get_available_language,
        mock__add_available_options_for_line,
    ):
        mock_line_item_repository = Mock()

        mock_line_item_repository.load_line_option_codes_for_line_code.return_value = []
        expected_data = [
            create_test_line_item(
                series="BMW_best_series", model_code="model_code", line_code="line_code"
            )
        ]
        mock_parse_model_matrix_to_line_items.return_value = expected_data
        mock_get_model_matrix.return_value = {"key": "test_key"}
        mock__get_available_language.return_value = "de"
        mock__add_available_options_for_line.side_effect = HTTPError()
        bmw_scraper = BMWScraper(mock_line_item_repository, self.scraper_config)
        bmw_scraper._scrape_models_for_market(Market.DE)

        mock_line_item_repository.load_line_option_codes_for_line_code.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.BMW,
            series="BMW_best_series",
            model_code="model_code",
            line_code="line_code",
        )

    @patch("src.price_monitor.price_scraper.bmw.scraper.get_updated_token")
    @patch.object(BMWScraper, "_scrape_models_for_market")
    def test_scrape_models_when_scraped_models_for_market_return_line_items_then_return_line_items(
        self,
        mock_scrape_models_for_market,
        mock_get_updated_token,
    ):
        expected_data = [create_test_line_item(model_description="bmw_line_item")]
        mock_session = Mock()
        mock_session.get.return_value = Mock(text="Model BMW Best You've Ever Seen")
        mock_get_updated_token.return_value = "x-token"
        mock_scrape_models_for_market.return_value = expected_data

        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "markets", [Market.DE])

        result = bmw_scraper.scrape_models(Market.DE)

        mock_scrape_models_for_market.assert_called_with(market=Market.DE)
        assert result == expected_data

    @patch("src.price_monitor.price_scraper.bmw.scraper.get_updated_token")
    @patch.object(BMWScraper, "_scrape_models_for_market")
    def test_scrape_models_when_scraped_models_for_market_returns_0_models_then_load_previous_models(
        self, mock_scrape_models_for_market, mock_get_updated_token
    ):
        mock_session = Mock()
        previos_day_models = [
            create_test_line_item(model_description="bmw_line_item"),
        ]
        mock_session.get.return_value = Mock(text="Model BMW Best You've Ever Seen")
        mock_scrape_models_for_market.return_value = []
        mock_line_item_repository = Mock()
        mock_get_updated_token.return_value = "x-token"
        mock_line_item_repository.load_market.return_value = previos_day_models

        bmw_scraper = BMWScraper(mock_line_item_repository, self.scraper_config)
        setattr(bmw_scraper, "session", mock_session)

        bmw_scraper.scrape_models(Market.DE)

        mock_line_item_repository.load_market.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.BMW,
        )
        mock_scrape_models_for_market.assert_called_with(market=Market.DE)

    @patch("src.price_monitor.price_scraper.bmw.scraper.scrape_models_for_usa")
    @patch("src.price_monitor.price_scraper.bmw.scraper.get_updated_token")
    def test_scraped_models_when_market_is_us_then_scrape_for_us(
        self, mock_get_updated_token, mock_scrape_models_for_usa
    ):
        expected_data = [
            create_test_line_item(model_description="bmw_line_item"),
        ]
        mock_scrape_models_for_usa.return_value = expected_data
        config = self.scraper_config
        config["scraper"]["enabled"] = {Vendor.BMW: [Market.US]}

        bmw_scraper = BMWScraper(FileSystemLineItemRepository, config)
        setattr(bmw_scraper, "market", Market.US)

        result = bmw_scraper.scrape_models(Market.US)

        assert result == expected_data
        assert mock_scrape_models_for_usa.call_count == 1

    @patch("src.price_monitor.price_scraper.bmw.scraper.adjust_line_options")
    @patch.object(BMWScraper, "get_options_price")
    @patch.object(BMWScraper, "add_available_options")
    @patch("src.price_monitor.price_scraper.bmw.scraper.parse_is_volt_48")
    @patch("src.price_monitor.price_scraper.bmw.scraper.parse_configuration_state")
    @patch(
        "src.price_monitor.price_scraper.bmw.scraper.get_configuration_state_and_is_volt_48"
    )
    @patch.object(BMWScraper, "get_available_options_for_model")
    @patch("src.price_monitor.price_scraper.bmw.scraper.parse_tax_date")
    @patch("src.price_monitor.price_scraper.bmw.scraper.parse_effect_date")
    @patch("src.price_monitor.price_scraper.bmw.scraper.parse_lines_string")
    def test__add_available_options_for_line_when_able_to_fetch_option_then_add_extra_options(
        self,
        mock_parse_lines_string,
        mock_parse_effect_date,
        mock_parse_tax_date,
        mock_get_available_options_for_model,
        mock_get_configuration_state_and_is_volt_48,
        mock_parse_configuration_state,
        mock_parse_is_volt_48,
        mock_add_available_options,
        mock_get_options_price,
        mock_adjust_line_options,
    ):
        line_item = create_test_line_item(
            vendor=Vendor.BMW,
            model_code="model_code",
            line_code="line_code",
            model_description="model_description",
            line_description="line_description",
            line_option_codes=[],
        )

        line_item_option_code = create_test_line_item_option_code(code="xyz")

        mock_session = Mock()
        model_matrix = Mock("Model Matrix Json")

        mock_get_available_options_for_model.return_value = {}

        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )

        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "IX_MODELS", [])

        mock_adjust_line_options.return_value = [line_item_option_code]

        actual_line_item = bmw_scraper._add_available_options_for_line(
            Market.DE, line_item, model_matrix
        )

        assert (
            line_item_option_code.asdict()
            == actual_line_item.line_option_codes[0].asdict()
        )
        mock_parse_lines_string.assert_called_with(model_matrix, line_item)

    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    @patch.object(BMWScraper, "_generate_get_request")
    def test_get_available_options_for_model_when_api_data_is_valid_return_data(
        self, mock__generate_get_request, mock_execute_request
    ):
        expected_data = {"data": Mock("I am data")}
        mock_session = Mock()

        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        mock__generate_get_request.return_value = "available_option_url"
        mock_execute_request.return_value = expected_data

        headers = {"Content-Type": "application/json", "x-api-key": "token_123"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "req_header", headers)

        result = bmw_scraper.get_available_options_for_model(
            "model_code", "2023-02-03", "2023-02-04"
        )

        mock__generate_get_request.assert_called_with(
            req_type="localisation_vehicle_check",
            model_code="model_code",
            effect_date="2023-02-03",
            tax_date="2023-02-04",
        )

        mock_execute_request.assert_called_with(
            "get",
            "available_option_url",
            mock_session,
            headers={"Content-Type": "application/json", X_API_KEY: "token_123"},
        )
        assert expected_data == result

    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    @patch.object(BMWScraper, "_generate_get_request")
    def test_get_available_options_for_model_when_api_data_is_not_valid_then_throws_value_error(
        self, mock__generate_get_request, mock_execute_request
    ):
        expected_data = "Wrong Option Type"
        mock_session = Mock()

        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        mock__generate_get_request.return_value = "available_option_url"
        mock_execute_request.return_value = expected_data

        headers = {"Content-Type": "application/json", "x-api-key": "token_123"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "req_header", headers)

        with self.assertRaises(ValueError):
            bmw_scraper.get_available_options_for_model(
                "model_code", "2023-02-03", "2023-02-04"
            )

        mock__generate_get_request.assert_called_with(
            req_type="localisation_vehicle_check",
            model_code="model_code",
            effect_date="2023-02-03",
            tax_date="2023-02-04",
        )
        mock_execute_request.assert_called_with(
            "get",
            "available_option_url",
            mock_session,
            headers={"Content-Type": "application/json", X_API_KEY: "token_123"},
        )

    def test__generate_get_request_when_req_type_localisation_vehicle_check_then_returns_localisation_vehicle_check_url(
        self,
    ):
        expected_url = "https://prod.ucp.bmw.cloud/localisations/overridden-vehicle-data/sources/pcaso/brands/bmwCar/countries/de/effect-dates/None/order-dates/None/applications/connext/models/model_code/options/languages/de/de?closest-fallback=true"
        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        language_support = {Market.DE: "de/de"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "IX_MODELS", [])
        setattr(bmw_scraper, "language_support", language_support)

        actual_url = bmw_scraper._generate_get_request(
            "localisation_vehicle_check", model_code="model_code"
        )

        assert expected_url == actual_url

    def test__generate_get_request_when_req_type_constructibility_check_then_returns_constructibility_check_url(
        self,
    ):
        expected_url = "https://prod.ucp.bmw.cloud/rulesolver/constructibility-check/configuration-state/None/add-element-bulk-invocation/None?excluded-elements=&mandatory-elements=None"
        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        language_support = {Market.DE: "de/de"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "IX_MODELS", [])
        setattr(bmw_scraper, "language_support", language_support)

        actual_url = bmw_scraper._generate_get_request(
            "constructibility_check", model_code="model_code"
        )

        assert expected_url == actual_url

        expected_url = "https://prod.ucp.bmw.cloud/rulesolver/constructibility-check/configuration-state/None/add-element-bulk-invocation/None?excluded-elements=None&mandatory-elements="

        actual_url = bmw_scraper._generate_get_request(
            "constructibility_check", model_code="model_code", line_code="BASIC_LINE"
        )

        assert expected_url == actual_url

    def test__generate_get_request_when_req_type_package_pricing_then_returns_package_pricing_url(
        self,
    ):
        expected_url = f"https://prod.ucp.bmw.cloud/pricing/calculation/public-calculation/price-lists/pcaso,con/brands/bmwCar/countries/de/models/model_code/tax-dates/None/package-pricing?effect-date=None&order-date={today_dashed_str()}&option-codes=None&ignore-invalid-option-codes=true&ignore-options-with-undefined-prices=true&params.isVolt48Variant=null&rounding-scale=1"
        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        language_support = {Market.DE: "de/de"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "IX_MODELS", [])
        setattr(bmw_scraper, "language_support", language_support)

        actual_url = bmw_scraper._generate_get_request(
            "package_pricing", model_code="model_code"
        )

        assert expected_url == actual_url

    @patch("src.price_monitor.price_scraper.bmw.scraper.parse_packages_price")
    @patch.object(BMWScraper, "get_packages_price")
    @patch("src.price_monitor.price_scraper.bmw.scraper.parse_options_price")
    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    @patch.object(BMWScraper, "generate_pricing_request_body")
    def test_get_options_price_when_api_return_valid_options_then_return_option_price_dict(
        self,
        mock_generate_pricing_request_body,
        mock_execute_request,
        mock_parse_options_price,
        mock_get_packages_price,
        mock_parse_packages_price,
    ):
        expected_options = {"option1": 15, "option2": 13}

        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        mock_session = Mock()

        headers = {"Content-Type": "application/json", "x-api-key": "token_123"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "req_header", headers)
        mock_generate_pricing_request_body.return_value = ["option_price_url", "body"]
        mock_execute_request.return_value = {"availableOptions": ["option1", "option2"]}
        mock_parse_options_price.return_value = {"option1": 12, "option2": 13}
        mock_get_packages_price.return_value = "package_price_json"
        mock_parse_packages_price.return_value = {"option1": 15}

        actual_options = bmw_scraper.get_options_price(
            "model_code", [], [], "2023-02-02", "2023-02-02", True
        )

        mock_parse_options_price.assert_called_with(
            {"availableOptions": ["option1", "option2"]}
        )
        mock_get_packages_price.assert_called_with(
            "model_code", "2023-02-02", "2023-02-02", "", True
        )
        mock_parse_packages_price.assert_called_with("package_price_json")
        mock_generate_pricing_request_body.assert_called_with(
            model_code="model_code",
            options=[],
            available_options=[],
            tax_date="2023-02-02",
            effect_date="2023-02-02",
            is_volt_48_variant=True,
        )
        mock_execute_request.assert_called_with(
            "post",
            "option_price_url",
            mock_session,
            headers={"Content-Type": "application/json", X_API_KEY: "token_123"},
            body="body",
        )
        assert expected_options == actual_options

    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    @patch.object(BMWScraper, "generate_pricing_request_body")
    def test_get_options_price_when_api_return_invalid_options_then_throws_value_error(
        self, mock_generate_pricing_request_body, mock_execute_request
    ):
        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        mock_session = Mock()

        headers = {"Content-Type": "application/json", "x-api-key": "token_123"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "req_header", headers)
        mock_generate_pricing_request_body.return_value = ["option_price_url", "body"]
        mock_execute_request.return_value = "availableOption key not present"

        with self.assertRaises(ValueError):
            bmw_scraper.get_options_price(
                "model_code", [], [], "2023-02-02", "2023-02-02", True
            )

        mock_generate_pricing_request_body.assert_called_with(
            model_code="model_code",
            options=[],
            available_options=[],
            tax_date="2023-02-02",
            effect_date="2023-02-02",
            is_volt_48_variant=True,
        )
        mock_execute_request.assert_called_with(
            "post",
            "option_price_url",
            mock_session,
            headers={"Content-Type": "application/json", X_API_KEY: "token_123"},
            body="body",
        )

    def test_generate_pricing_request_body_when_required_detailed_pass_then_return_request_url_and_body_for_the_request(
        self,
    ):
        expected_url = "https://prod.ucp.bmw.cloud/pricing/calculation/public-calculation/price-lists/pcaso,con/brands/bmwCar/countries/de"
        expected_body = {
            "additionalParams": {
                "isVolt48Variant": {"key": "isVolt48Variant", "value": True}
            },
            "configuration": {
                "availableOptions": ["option2"],
                "model": "model_code",
                "selectedOptions": ["option1"],
            },
            "settings": {
                "accessoriesMustFitConfiguration": False,
                "ignoreInvalidOptionCodes": True,
                "ignoreOptionsWithUndefinedPrices": True,
                "priceTree": "DEFAULT",
                "roundingScale": 1,
            },
            "validityDates": {"effectDate": "2023-02-02", "taxDate": "2023-02-02"},
        }
        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "IX_MODELS", [])

        actual_url, actual_body = bmw_scraper.generate_pricing_request_body(
            "model_code", ["option1"], ["option2"], "2023-02-02", "2023-02-02", True
        )

        assert expected_url == actual_url
        assert expected_body == actual_body

    @patch(
        "src.price_monitor.price_scraper.bmw.scraper.parse_constructible_extra_options_for_line"
    )
    @patch.object(BMWScraper, "get_constructibility_check")
    @patch("src.price_monitor.price_scraper.bmw.scraper.parse_extra_available_options")
    def test_add_available_options_when_it_is_constructible_then_extend_the_list_of_option(
        self,
        mock_parse_extra_available_options,
        mock_get_constructibility_check,
        mock_parse_constructible_extra_options_for_line,
    ):
        expected_options = [
            create_test_line_item_option_code("included_option1"),
            create_test_line_item_option_code("included_option2"),
            create_test_line_item_option_code("extra_option1"),
        ]
        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        mock_session = Mock()
        line_item = create_test_line_item(
            vendor=Vendor.BMW,
            model_code="model_code",
            line_code="line_code",
            line_option_codes=[
                create_test_line_item_option_code("included_option1"),
                create_test_line_item_option_code("included_option2"),
            ],
        )

        headers = {"Content-Type": "application/json", "x-api-key": "token_123"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "req_header", headers)

        mock_parse_extra_available_options.return_value = "option1,option2"
        mock_get_constructibility_check.return_value = "constructibility_json"
        mock_parse_constructible_extra_options_for_line.return_value = [
            create_test_line_item_option_code("extra_option1")
        ]

        actual_options = bmw_scraper.add_available_options(
            line_item,
            "config-state-123",
            {"option1": "description", "option2": "description2"},
            "BASIC_LINE,M_PERFORMANCE_LINE",
        )

        mock_parse_extra_available_options.assert_called_with(
            {"option1": "description", "option2": "description2"},
            {"included_option2", "included_option1"},
            "BASIC_LINE,M_PERFORMANCE_LINE",
        )
        mock_get_constructibility_check.assert_called_with(
            "model_code",
            "line_code",
            "option1,option2",
            "config-state-123",
            "BASIC_LINE,M_PERFORMANCE_LINE",
        )
        mock_parse_constructible_extra_options_for_line.assert_called_with(
            "constructibility_json"
        )
        assert expected_options == actual_options

    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    @patch.object(BMWScraper, "_generate_get_request")
    def test_get_constructibility_check_when_api_return_valid_dict_then_return_constructibility_json(
        self,
        mock__generate_get_request,
        mock_execute_request,
    ):
        expected_json = {"option1": {"isConstructible": True}}
        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        mock_session = Mock()

        headers = {"Content-Type": "application/json", "x-api-key": "token_123"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "req_header", headers)
        setattr(bmw_scraper, "IX_MODELS", [])
        mock__generate_get_request.return_value = "constructablity_url"
        mock_execute_request.return_value = expected_json

        actual_json = bmw_scraper.get_constructibility_check(
            "model_code",
            "line_code",
            "option1,option2",
            "configuration-state-12",
            "BASIC_LINE,M_PERFORMANCE_LINE",
        )

        mock__generate_get_request.assert_called_with(
            req_type="constructibility_check",
            model_code="model_code",
            line_code="line_code",
            options_str="option1,option2",
            configuration_state="configuration-state-12",
            lines_str="BASIC_LINE,M_PERFORMANCE_LINE",
        )
        mock_execute_request.assert_called_with(
            "get",
            "constructablity_url",
            mock_session,
            headers={"Content-Type": "application/json", X_API_KEY: "token_123"},
        )
        assert expected_json == actual_json

    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    @patch.object(BMWScraper, "_generate_get_request")
    def test_get_constructibility_check_when_api_return_invalid_response_then_throws_error(
        self,
        mock__generate_get_request,
        mock_execute_request,
    ):
        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        mock_session = Mock()

        headers = {"Content-Type": "application/json", "x-api-key": "token_123"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "req_header", headers)
        mock__generate_get_request.return_value = "constructablity_url"
        mock_execute_request.return_value = "Wrong Response"

        with self.assertRaises(ValueError):
            bmw_scraper.get_constructibility_check(
                "model_code",
                "line_code",
                "option1,option2",
                "configuration-state-12",
                "BASIC_LINE,M_PERFORMANCE_LINE",
            )

        mock__generate_get_request.assert_called_with(
            req_type="constructibility_check",
            model_code="model_code",
            line_code="line_code",
            options_str="option1,option2",
            configuration_state="configuration-state-12",
            lines_str="BASIC_LINE,M_PERFORMANCE_LINE",
        )
        mock_execute_request.assert_called_with(
            "get",
            "constructablity_url",
            mock_session,
            headers={"Content-Type": "application/json", X_API_KEY: "token_123"},
        )

    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    @patch.object(BMWScraper, "_generate_get_request")
    def test_get_packages_price_when_api_return_valid_response_then_return_packages_price_json(
        self,
        mock__generate_get_request,
        mock_execute_request,
    ):
        expected_json = {"packagePricingList": [{"option1": 300}]}

        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        mock_session = Mock()

        headers = {"Content-Type": "application/json", "x-api-key": "token_123"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "req_header", headers)
        mock__generate_get_request.return_value = "packages_price_url"
        mock_execute_request.return_value = expected_json

        actual_json = bmw_scraper.get_packages_price(
            "model_code", "line_code", "2023-02-02", "option1,option2", True
        )

        mock__generate_get_request.assert_called_with(
            req_type="package_pricing",
            model_code="model_code",
            effect_date="line_code",
            tax_date="2023-02-02",
            options_str="option1,option2",
            is_volt_48_variant=True,
        )
        mock_execute_request.assert_called_with(
            "get",
            "packages_price_url",
            mock_session,
            headers={"Content-Type": "application/json", X_API_KEY: "token_123"},
        )
        assert expected_json == actual_json

    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    @patch.object(BMWScraper, "_generate_get_request")
    def test_get_packages_price_when_api_return_invalid_response_then_throws_error(
        self,
        mock__generate_get_request,
        mock_execute_request,
    ):
        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        mock_session = Mock()

        headers = {"Content-Type": "application/json", "x-api-key": "token_123"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "req_header", headers)
        mock__generate_get_request.return_value = "package_pricing_url"
        mock_execute_request.return_value = "Wrong Response"

        with self.assertRaises(ValueError):
            bmw_scraper.get_packages_price(
                "model_code", "line_code", "2023-02-02", "option1,option2", True
            )

        mock__generate_get_request.assert_called_with(
            req_type="package_pricing",
            model_code="model_code",
            effect_date="line_code",
            tax_date="2023-02-02",
            options_str="option1,option2",
            is_volt_48_variant=True,
        )

        mock_execute_request.assert_called_with(
            "get",
            "package_pricing_url",
            mock_session,
            headers={"Content-Type": "application/json", X_API_KEY: "token_123"},
        )

    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    @patch.object(BMWScraper, "_generate_get_request")
    def test_get_configuration_state_and_is_volt_48_when_api_return_valid_response_then_return_json(
        self,
        mock__generate_get_request,
        mock_execute_request,
    ):
        expected_json = {"classifiedConfiguration": "config-state1"}
        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        mock_session = Mock()

        headers = {"Content-Type": "application/json", "x-api-key": "token_123"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "req_header", headers)
        mock__generate_get_request.return_value = "state_and_is_volt_48_url"
        mock_execute_request.return_value = expected_json

        actual_json = get_configuration_state_and_is_volt_48(
            "model_code",
            "2023-02-02",
            "option1,option2",
            [],
            headers,
            mock_session,
            Market.DE,
        )

        mock_execute_request.assert_called_with(
            "get",
            f"https://prod.ucp.bmw.cloud/rulesolver/constructibility-check/rule-sets/pcaso,con/brands/bmwCar/countries/de/effect-dates/2023-02-02/order-dates/{today_dashed_str()}/models/model_code?included-elements=option1,option2&mandatory-elements=&add-rules-for-mandatory-element-classes=fabric,paint,rim&debug=false",
            mock_session,
            headers={"Content-Type": "application/json", X_API_KEY: "token_123"},
        )
        assert expected_json == actual_json

    @patch("src.price_monitor.price_scraper.bmw.scraper.execute_request")
    @patch.object(BMWScraper, "_generate_get_request")
    def test_get_configuration_state_and_is_volt_48_when_api_return_invalid_response_then_throws_error(
        self,
        mock__generate_get_request,
        mock_execute_request,
    ):
        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        mock_session = Mock()

        headers = {"Content-Type": "application/json", "x-api-key": "token_123"}

        setattr(bmw_scraper, "market", Market.DE)
        setattr(bmw_scraper, "session", mock_session)
        setattr(bmw_scraper, "req_header", headers)
        mock__generate_get_request.return_value = "state_and_is_volt_48_url"
        mock_execute_request.return_value = "Wrong Response"

        with self.assertRaises(ValueError):
            get_configuration_state_and_is_volt_48(
                "model_code",
                "2023-02-02",
                "option1,option2",
                [],
                headers,
                mock_session,
                Market.DE,
            )

        mock_execute_request.assert_called_with(
            "get",
            f"https://prod.ucp.bmw.cloud/rulesolver/constructibility-check/rule-sets/pcaso,con/brands/bmwCar/countries/de/effect-dates/2023-02-02/order-dates/{today_dashed_str()}/models/model_code?included-elements=option1,option2&mandatory-elements=&add-rules-for-mandatory-element-classes=fabric,paint,rim&debug=false",
            mock_session,
            headers={"Content-Type": "application/json", X_API_KEY: "token_123"},
        )

    @patch("src.price_monitor.price_scraper.bmw.scraper.requests")
    @patch("src.price_monitor.price_scraper.bmw.scraper._get_available_language")
    @patch("src.price_monitor.price_scraper.bmw.scraper.get_ix_models")
    @patch.object(BMWScraper, "append_available_options")
    @patch(
        "src.price_monitor.price_scraper.bmw.scraper.parse_model_matrix_to_line_items"
    )
    @patch("src.price_monitor.price_scraper.bmw.scraper.get_model_matrix")
    def test__scrape_models_for_market_should_be_able_to_scrape_ix_models_for_uk(
        self,
        mock_get_model_matrix,
        mock_parse_model_matrix_to_line_items,
        mock_append_available_options,
        mock_get_ix_models,
        mock__get_available_language,
        mock_requests,
    ):
        mock_get_model_matrix.return_value = {"language": "en/GB", "models": []}
        mock__get_available_language.return_value = "en/GB"
        mock_parse_model_matrix_to_line_items.return_value = [
            create_test_line_item(),
            create_test_line_item(),
        ]
        mock_append_available_options.side_effect = [
            [],
            [
                create_test_line_item(),
                create_test_line_item(),
            ],
        ]
        mock_get_ix_models.return_value = [
            {},
            [create_test_line_item(), create_test_line_item()],
        ]
        mock_session = Mock()
        bmw_scraper = BMWScraper(
            FileSystemLineItemRepository,
            self.scraper_config,
        )
        mock_requests.Session.return_value = mock_session
        result = bmw_scraper._scrape_models_for_market(Market.UK)

        assert mock_get_model_matrix.call_count == 1
        assert mock_append_available_options.call_count == 2
        mock_get_model_matrix.assert_called_with(
            Market.UK, mock_session, {"Content-Type": "application/json"}
        )
        mock_parse_model_matrix_to_line_items.assert_called_with(
            {"language": "en/GB", "models": []}, Market.UK
        )
        assert len(result) == 2

    @patch(
        "src.price_monitor.price_scraper.bmw.scraper.parse_model_matrix_to_line_items"
    )
    @patch("src.price_monitor.price_scraper.bmw.scraper.get_model_matrix")
    def test_get_ix_models(
        self, mock_get_model_matrix, mock_parse_model_matrix_to_line_items
    ):
        expected_model_matrix = {"I": {"modelRanges": {"models": ["IXMA", "IXMB"]}}}
        expected_ix_line_items = [
            create_test_line_item(vendor=Vendor.BMW, series="I", model_code="IXMA"),
            create_test_line_item(vendor=Vendor.BMW, series="I", model_code="IXMB"),
        ]
        mock_get_model_matrix.return_value = expected_model_matrix
        mock_parse_model_matrix_to_line_items.return_value = expected_ix_line_items
        mock_session = Mock()
        actual_model_matrix, actual_i_line_items = get_ix_models(
            Market.UK, {"application/json"}, mock_session
        )

        mock_get_model_matrix.assert_called_with(
            Market.UK,
            mock_session,
            {"application/json"},
            f"https://prod.ucp.bmw.cloud/model-matrices/vehicle-trees/connext-bmw/sources/pcaso/brands/bmwi/countries/gb/effect-dates/{today_dashed_str()}/order-dates/{today_dashed_str()}?closest-fallback=true",
        )
        mock_parse_model_matrix_to_line_items.assert_called_with(
            expected_model_matrix, Market.UK
        )
        assert expected_model_matrix == actual_model_matrix
        assert expected_ix_line_items == actual_i_line_items
