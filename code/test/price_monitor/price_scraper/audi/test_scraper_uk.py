import unittest
from test.price_monitor.utils.test_data_builder import (
    create_test_line_item,
    create_test_line_item_option_code,
)
from unittest.mock import Mock, patch

from requests import HTTPError

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.audi.constants import AUDI_UK_CONFIG_URL
from src.price_monitor.price_scraper.audi.scraper import AudiScraper
from src.price_monitor.price_scraper.audi.scraper_uk import AudiScraperUK
from src.price_monitor.utils.clock import (
    today_dashed_str,
    yesterday_dashed_str_with_key,
)


def mocked_execute_request(method: str, url: str, session=Mock()):
    if url == "https://www.audi.co.uk/uk/web/en/models//xx.carinfo.mv-0-1216.10.json":
        return {"configuration": {"carlineName": ""}}
    elif (
        url
        == "https://www.audi.co.uk/uk/web/en/models//xx.modelsinfo.mv-0-1216.10.json"
    ):
        return {"models": "audi_line_item_for_model_1"}


class TestAudiUKScraper(unittest.TestCase):
    @patch(
        "src.price_monitor.price_scraper.audi.scraper.AudiScraper._scrape_models_for_market"
    )
    def test_scrape_models_loads_yesterdays_data_when_scrape_models_for_market_returns_empty_list_of_models(
        self, mock_scrape_models_for_market
    ):
        audi_scraper_config = {
            "scraper": {"enabled": {Vendor.AUDI: [Market.UK]}},
            "feature_toggle": {"is_audi_enabled_for_US": True},
        }
        mock_scrape_models_for_market.return_value = []

        mock_line_item_repository = Mock()
        mock_line_item_repository.load_market.return_value = []

        audi_scraper = AudiScraper(
            mock_line_item_repository,
            audi_scraper_config,
        )

        audi_scraper.scrape_models(Market.UK)

        mock_line_item_repository.load_market.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.UK,
            vendor=Vendor.AUDI,
        )

    @patch.object(AudiScraperUK, "_scrape_models_from_model_range")
    @patch(
        "src.price_monitor.price_scraper.audi.scraper_uk.parse_available_model_range_links"
    )
    @patch("src.price_monitor.price_scraper.audi.scraper_uk.execute_request")
    def test_scrape_models_for_uk_loads_yesterdays_models_for_a_model_range_when_scrape_models_from_model_range_returns_fails(
        self,
        mock_execute_request,
        mock_parse_available_model_range_links,
        mock_scrape_models_from_model_range,
    ):
        mock_execute_request.return_value = "home page text"
        mock_parse_available_model_range_links.return_value = ["a4/a4-limousine"]
        mock_scrape_models_from_model_range.side_effect = [
            HTTPError(),
        ]
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_model_filter_by_model_range_code.return_value = [
            create_test_line_item(model_code="model_previous")
        ]

        scraper = AudiScraperUK(mock_line_item_repository, session=Mock(), config={})
        line_items = scraper.scrape_models_for_uk()

        mock_parse_available_model_range_links.assert_called_with("home page text")
        mock_line_item_repository.load_model_filter_by_model_range_code.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.UK,
            vendor=Vendor.AUDI,
            series="a4",
            model_range_code="a4-limousine",
        )
        assert len(line_items) == 1

    @patch.object(AudiScraperUK, "_scrape_models_from_model_range")
    @patch(
        "src.price_monitor.price_scraper.audi.scraper_uk.parse_available_model_range_links"
    )
    @patch("src.price_monitor.price_scraper.audi.scraper_uk.execute_request")
    def test_scrape_models_for_uk_extends_models_when_scrape_models_from_model_range_returns_line_items(
        self,
        mock_execute_request,
        mock_parse_available_model_range_links,
        mock_scrape_models_from_model_range,
    ):
        mock_execute_request.return_value = "home page text"
        mock_parse_available_model_range_links.return_value = ["a4/a4-limousine"]

        mock_scrape_models_from_model_range.return_value = [
            create_test_line_item(model_code="model_code")
        ]

        scraper = AudiScraperUK(
            line_item_repository=Mock(),
            session=Mock(),
            config={},
        )
        actual_line_items = scraper.scrape_models_for_uk()

        mock_parse_available_model_range_links.assert_called_with("home page text")
        mock_scrape_models_from_model_range.assert_called_with("a4/a4-limousine")
        assert len(actual_line_items) == 1

    list_test_line_item = [
        create_test_line_item(
            line_option_codes=[
                create_test_line_item_option_code(code="list_line_item_xx")
            ]
        )
    ]

    @patch(
        "src.price_monitor.price_scraper.audi.scraper_uk.execute_request",
        side_effect=mocked_execute_request,
    )
    @patch(
        "src.price_monitor.price_scraper.audi.scraper_uk.AudiScraperUK._get_line_items_for_model",
        return_value=list_test_line_item,
    )
    def test__scrape_models_from_model_range_extends_list_with_model_line_items(
        self,
        mock_get_line_items_for_model,
        mock_execute_request,
    ):
        mock_link = "/xx"
        mock_line_item_repository = Mock()
        scraper = AudiScraperUK(mock_line_item_repository, session=Mock(), config={})
        line_items = scraper._scrape_models_from_model_range(mock_link)
        line_item_option_code = self.list_test_line_item
        mock_get_line_items_for_model.return_value = line_item_option_code

        assert line_items == line_item_option_code

    @patch("src.price_monitor.price_scraper.audi.scraper_uk.parse_model_line_item")
    @patch("src.price_monitor.price_scraper.audi.scraper_uk.parse_line_option_codes")
    @patch("src.price_monitor.price_scraper.audi.scraper_uk.execute_request")
    def test__get_line_items_for_model_when_response_does_not_contain_prices_but_contains_choice_ids_executes_new_request_and_returns_models_data(
        self,
        mock_execute_request,
        mock_parse_line_option_codes,
        mock_parse_model_line_item,
    ):
        test_model_details = {
            "audi_line_item_for_model_1": {
                "details": "audi_line_item_for_model_1_detail",
                "max-output": "",
            }
        }
        test_config_data = {
            "items": [],
            "configuration": {"items": ["configuration_item_1"]},
            "families": {},
        }
        test_link = "xx"
        mock_session = Mock()

        total_raw_price = 10000
        car_line_name = "e-tron"
        model = "Audi Q8 e-tron"
        description = "Audi Q8 e-tron description"

        mock_execute_request.return_value = {
            "header": "error",
            "configuration": {},
            "conflicts": {"choiceIds": {}, "prstring": "parameter_test"},
        }
        mock_parse_model_line_item.return_value = create_test_line_item(
            recorded_at=today_dashed_str(),
            vendor=Vendor.AUDI,
            model_range_description=car_line_name,
            model_code=model,
            model_description=description,
            net_list_price=total_raw_price,
            gross_list_price=total_raw_price,
            market=Market.UK,
        )

        mock_line_item_repository = Mock()

        mock_parse_line_option_codes.return_value = create_test_line_item_option_code(
            code="Line option code for e-tron"
        )

        scraper = AudiScraperUK(mock_line_item_repository, mock_session, config={})
        assert scraper._get_line_items_for_model(
            test_model_details,
            test_config_data,
            test_link,
        ) == [
            create_test_line_item(
                recorded_at=today_dashed_str(),
                vendor=Vendor.AUDI,
                model_range_description=car_line_name,
                model_code=model,
                model_description=description,
                net_list_price=total_raw_price,
                gross_list_price=total_raw_price,
                market=Market.UK,
                line_option_codes=create_test_line_item_option_code(
                    code="Line option code for e-tron"
                ),
            )
        ]

        mock_execute_request.assert_called_with(
            "get",
            AUDI_UK_CONFIG_URL,
            mock_session,
            body={"ids": "parameter_test", "action": "accept"},
        )

    @patch("src.price_monitor.price_scraper.audi.scraper_uk.parse_model_line_item")
    @patch("src.price_monitor.price_scraper.audi.scraper_uk.parse_line_option_codes")
    @patch("src.price_monitor.price_scraper.audi.scraper_uk.execute_request")
    def test__get_line_items_for_model_when_response_contains_prices_returns_models_data(
        self,
        mock_execute_request,
        mock_parse_line_option_codes,
        mock_parse_model_line_item,
    ):
        test_model_details = {
            "audi_line_item_for_model_1": {
                "details": "audi_line_item_for_model_1_detail",
                "max-output": "",
            }
        }
        test_config_data = {
            "items": [],
            "configuration": {"items": ["configuration_item_1"]},
            "families": {},
        }
        test_link = "xx"
        mock_session = Mock()

        total_raw_price = 10000
        car_line_name = "e-tron"
        model = "Audi Q8 e-tron"
        description = "Audi Q8 e-tron description"

        mock_execute_request.return_value = {
            "configuration": {
                "prices": {"totalRaw": 1000},
                "carlineName": car_line_name,
                "model": model,
                "description": description,
            }
        }
        mock_parse_model_line_item.return_value = create_test_line_item(
            recorded_at=today_dashed_str(),
            vendor=Vendor.AUDI,
            model_range_description=car_line_name,
            model_code=model,
            model_description=description,
            net_list_price=total_raw_price,
            gross_list_price=total_raw_price,
            market=Market.UK,
        )

        mock_line_item_repository = Mock()

        mock_parse_line_option_codes.return_value = create_test_line_item_option_code(
            code="Line option code for e-tron"
        )

        scraper = AudiScraperUK(mock_line_item_repository, mock_session, config={})
        assert scraper._get_line_items_for_model(
            test_model_details,
            test_config_data,
            test_link,
        ) == [
            create_test_line_item(
                recorded_at=today_dashed_str(),
                vendor=Vendor.AUDI,
                model_range_description=car_line_name,
                model_code=model,
                model_description=description,
                net_list_price=total_raw_price,
                gross_list_price=total_raw_price,
                market=Market.UK,
                line_option_codes=create_test_line_item_option_code(
                    code="Line option code for e-tron"
                ),
            )
        ]

        mock_execute_request.assert_called_with(
            "get",
            AUDI_UK_CONFIG_URL,
            mock_session,
            body={
                "ids": "configuration_item_1",
                "set": "audi_line_item_for_model_1",
            },
        )

    @patch("src.price_monitor.price_scraper.audi.scraper_uk.parse_model_line_item")
    @patch("src.price_monitor.price_scraper.audi.scraper_uk.parse_line_option_codes")
    @patch("src.price_monitor.price_scraper.audi.scraper_uk.execute_request")
    def test__get_line_items_for_model_when_response_does_not_contains_prices_neither_choices_returns_empty_models_data(
        self,
        mock_execute_request,
        mock_parse_line_option_codes,
        mock_parse_model_line_item,
    ):
        test_model_details = {
            "audi_line_item_for_model_1": {
                "details": "audi_line_item_for_model_1_detail",
                "max-output": "",
            }
        }
        test_config_data = {
            "configuration": {"items": []},
            "conflicts": {},
            "items": [],
            "families": {},
        }
        test_link = "xx"
        mock_session = Mock()
        mock_line_item_repository = Mock()

        mock_execute_request.return_value = {}

        scraper = AudiScraperUK(mock_line_item_repository, mock_session, config={})
        assert (
            scraper._get_line_items_for_model(
                test_model_details,
                test_config_data,
                test_link,
            )
            == []
        )

        mock_execute_request.assert_called_once()

    @patch("src.price_monitor.price_scraper.audi.scraper_uk.parse_model_line_item")
    @patch("src.price_monitor.price_scraper.audi.scraper_uk.parse_line_option_codes")
    @patch("src.price_monitor.price_scraper.audi.scraper_uk.execute_request")
    def test__get_line_items_for_model_when_response_contains_empty_prices_and_empty_choices_returns_empty_models_data(
        self,
        mock_execute_request,
        mock_parse_line_option_codes,
        mock_parse_model_line_item,
    ):
        test_model_details = {
            "audi_line_item_for_model_1": {
                "details": "audi_line_item_for_model_1_detail",
                "max-output": "",
            }
        }
        test_config_data = {
            "configuration": {"items": []},
            "conflicts": {},
            "families": {},
            "items": [],
        }
        test_link = "xx"
        mock_session = Mock()

        mock_execute_request.return_value = {"configuration": {}, "conflicts": {}}
        mock_parse_line_option_codes.return_value = []
        mock_line_item_repository = Mock()
        scraper = AudiScraperUK(mock_line_item_repository, mock_session, config={})

        assert (
            scraper._get_line_items_for_model(
                test_model_details,
                test_config_data,
                test_link,
            )
            == []
        )

        mock_execute_request.assert_called_once()

    @patch("src.price_monitor.price_scraper.audi.scraper_uk.parse_line_option_codes")
    @patch("src.price_monitor.price_scraper.audi.scraper_uk.execute_request")
    def test__get_line_items_for_model_when_execute_request_throws_http_error_then_previous_day_data_should_load(
        self,
        mock_execute_request,
        mock_parse_line_option_codes,
    ):
        expected_line_item = create_test_line_item(
            vendor=Vendor.AUDI, model_code="a4-sedan"
        )

        mock_execute_request.side_effect = HTTPError()
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_model_filter_by_model_code.return_value = [
            expected_line_item
        ]

        test_model_details = {
            "audi_line_item_for_model_1": {
                "details": "audi_line_item_for_model_1_detail",
                "max-output": "",
            }
        }
        test_config_data = {
            "configuration": {"items": []},
            "conflicts": {},
            "items": [],
            "families": {},
        }
        test_link = "xx"
        mock_session = Mock()

        mock_execute_request.return_value = {"configuration": {}, "conflicts": {}}
        mock_parse_line_option_codes.return_value = []

        scraper = AudiScraperUK(
            line_item_repository=mock_line_item_repository,
            session=mock_session,
            config={},
        )
        assert (
            scraper._get_line_items_for_model(
                test_model_details,
                test_config_data,
                test_link,
            )[0]
            == expected_line_item
        )
        mock_line_item_repository.load_model_filter_by_model_code.assert_called_with(
            date=yesterday_dashed_str_with_key(),
            market=Market.UK,
            vendor=Vendor.AUDI,
            model_code="audi_line_item_for_model_1",
        )

        mock_execute_request.assert_called_once()
