import unittest
from pathlib import Path
from test.price_monitor.utils.test_data_builder import create_test_line_item
from unittest.mock import Mock, call, patch

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.parser_usa import (
    AvailableModel,
    AvailableTrimLine,
)
from src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa import (
    MercedesBenzUSAScraper,
)
from src.price_monitor.utils.clock import (
    today_dashed_str_with_key,
    yesterday_dashed_str,
)


class TestMercedesBenzUSAScraper(unittest.TestCase):
    TEST_DATA_DIR = f"{Path(__file__).parent}/sample_usa_apis"

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.execute_all_models_request",
        return_value={},
    )
    def test_get_models_returns_empty_list_when_api_returns_no_items(
        self, mock_request
    ):
        scraper = MercedesBenzUSAScraper(
            line_item_repository=Mock(), session=Mock(), config={}
        )
        assert scraper._get_models() == []

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.MercedesBenzUSAParser.parse_available_models"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.execute_all_models_request"
    )
    def test_get_models_returns_parsed_available_models_when_api_returns_models(
        self, mock_request, mock_parser
    ):
        model_payload = open(f"{self.TEST_DATA_DIR}/usa_models.json", "r")
        mock_request.return_value = model_payload

        scraper = MercedesBenzUSAScraper(
            line_item_repository=Mock(), session=Mock(), config={}
        )

        expected_models = [
            self.model_no_line,
        ]
        mock_parser.return_value = expected_models

        assert scraper._get_models() == expected_models

        model_payload.close()

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.execute_model_request"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.MercedesBenzUSAParser.parse_trim_line"
    )
    def test_get_basic_line_returns_line_item_with_basic_line_data(
        self, mock_parse, mock_request
    ):
        with open(f"{self.TEST_DATA_DIR}/cabriolet_base_model.html", "r") as payload:
            mock_request.return_value = payload

        scraper = MercedesBenzUSAScraper(
            line_item_repository=Mock(), session=Mock(), config={}
        )
        basic_model = AvailableModel(
            "model_code", False, "/en/vehicles/build/c-class/cabriolet/c300a"
        )
        mock_parse.return_value = self.line_item

        assert scraper._get_basic_line(basic_model) == self.line_item

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.execute_model_request"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.MercedesBenzUSAParser.parse_line_codes"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.MercedesBenzUSAParser.parse_trim_line"
    )
    def test_get_trim_line_returns_line_item_with_trim_line_data(
        self, mock_parse_trim_line, mock_parse_line_codes, mock_request
    ):
        model_html = open(f"{self.TEST_DATA_DIR}/sedan_model.html", "r")
        trim_line_html = open(f"{self.TEST_DATA_DIR}/sedan_trim_line.html", "r")
        trim_line2_html = open(f"{self.TEST_DATA_DIR}/sedan_trim_line.html", "r")
        mock_request.side_effect = [model_html, trim_line_html, trim_line2_html]

        trim_line_model = AvailableModel(
            "model_code", False, "/en/vehicles/build/c-class/cabriolet/c300a"
        )

        line_code_url = AvailableTrimLine(
            line_code="line_code",
            line_description="line_description",
            line_path="/line_code_path",
        )
        line_code_url2 = AvailableTrimLine(
            line_code="line_code2",
            line_description="line_description2",
            line_path="/line_code_path2",
        )
        mock_parse_line_codes.return_value = [line_code_url, line_code_url2]
        mock_parse_trim_line.side_effect = [self.line_item, self.line_item2]
        mock_session = Mock()

        scraper = MercedesBenzUSAScraper(
            line_item_repository=Mock(), session=mock_session, config={}
        )
        assert scraper._get_trim_lines(trim_line_model) == [
            self.line_item,
            self.line_item2,
        ]
        mock_request.assert_has_calls(
            [
                call(trim_line_model.build_page, mock_session),
                call("/line_code_path", mock_session),
                call("/line_code_path2", mock_session),
            ]
        )
        # mock_parse_trim_line.assert_has_calls([call(trim_line_html)])

        trim_line_html.close()
        trim_line2_html.close()
        model_html.close()

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.MercedesBenzUSAScraper._get_models"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.MercedesBenzUSAScraper._get_basic_line"
    )
    def test_scrape_models_calls_get_basic_line_when_line_exists_is_false(
        self,
        mock_get_basic_line,
        mock_get_models,
    ):
        scraper = MercedesBenzUSAScraper(
            line_item_repository=Mock(), session=Mock(), config={}
        )
        mock_get_models.return_value = [self.model_no_line]
        mock_get_basic_line.return_value = self.line_item

        assert scraper.scrape_models() == [self.line_item]

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.MercedesBenzUSAScraper._get_models"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.MercedesBenzUSAScraper._get_trim_lines"
    )
    def test_scrape_models_calls_get_trim_lines_when_line_exists_is_false(
        self,
        mock_get_trim_lines,
        mock_get_models,
    ):
        scraper = MercedesBenzUSAScraper(
            line_item_repository=Mock(), session=Mock(), config={}
        )
        mock_get_models.return_value = [self.model_with_line]
        mock_get_trim_lines.return_value = self.line_item_list

        assert scraper.scrape_models() == self.line_item_list

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.MercedesBenzUSAScraper._load_previous_day_line_items"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.execute_model_request"
    )
    def test__get_trim_lines_when_build_page_api_fails_then_return_previous_day_line_items(
        self,
        mock_execute_model_request,
        mock_load_previous_day_line_items,
    ):
        mock_execute_model_request.return_value = None
        model = AvailableModel(
            "model_code", False, "/en/vehicles/build/c-class/cabriolet/c300a"
        )
        expected_line_item = create_test_line_item(vendor=Vendor.MERCEDES_BENZ)
        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_load_previous_day_line_items.return_value = [expected_line_item]

        scraper = MercedesBenzUSAScraper(
            line_item_repository=mock_line_item_repository,
            session=mock_session,
            config={},
        )
        actual_line_items = scraper._get_trim_lines(model)

        mock_load_previous_day_line_items.assert_called_with(model)
        assert expected_line_item.asdict() == actual_line_items[0].asdict()

    def test__load_previous_day_line_items_calls_load_model_filter_by_model_code_and_returns_empty_list(
        self,
    ):
        mock_line_item_repo = Mock()
        mock_line_item_repo.load_model_filter_by_model_code.return_value = []

        scraper = MercedesBenzUSAScraper(mock_line_item_repo, Mock(), config={})

        available_model = AvailableModel("cool_code", True, "/cool/page")

        scraper._load_previous_day_line_items(available_model)

        mock_line_item_repo.load_model_filter_by_model_code.assert_called_with(
            date=yesterday_dashed_str(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
            model_code=available_model.model_code,
        )

    def test__load_previous_day_line_items_calls_load_model_filter_by_model_code_with_model(
        self,
    ):
        mock_line_item_repo = Mock()
        yesterday_line_item = create_test_line_item(recorded_at=yesterday_dashed_str())
        mock_line_item_repo.load_model_filter_by_model_code.return_value = [
            yesterday_line_item
        ]

        scraper = MercedesBenzUSAScraper(mock_line_item_repo, Mock(), config={})

        available_model = AvailableModel("cool_code", True, "/cool/page")

        assert scraper._load_previous_day_line_items(available_model) == [
            yesterday_line_item
        ]
        mock_line_item_repo.load_model_filter_by_model_code.assert_called_with(
            date=yesterday_dashed_str(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
            model_code=available_model.model_code,
        )

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.execute_model_request"
    )
    def test__get_trim_lines_when_line_page_api_fails_then_return_previous_day_line_item(
        self, mock_execute_model_request
    ):
        mock_execute_model_request.side_effect = ["page data", None]
        model = AvailableModel(
            "a535b", False, "/en/vehicles/build/c-class/cabriolet/c300a"
        )
        expected_line_item = create_test_line_item(
            vendor=Vendor.MERCEDES_BENZ,
            model_code=model.model_code,
        )

        mock_session = Mock()
        mock_line_item_repository = Mock()
        mock_line_item_repository.load_line_item_for_trim_line.return_value = (
            expected_line_item
        )

        mock_parser = Mock()
        mock_parser.extract_line_json_from_html.return_value = {"baumuster": "a535b"}
        mock_parser.parse_line_codes.return_value = [
            AvailableTrimLine(
                line_code="line_code",
                line_description="line_description",
                line_path="/line_code_path",
            )
        ]
        scraper = MercedesBenzUSAScraper(
            line_item_repository=mock_line_item_repository,
            session=mock_session,
            config={},
        )
        setattr(scraper, "parser", mock_parser)
        actual_line_items = scraper._get_trim_lines(model)

        mock_line_item_repository.load_line_item_for_trim_line.assert_called_with(
            date=yesterday_dashed_str(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
            model_code="a535b",
            line_code="line_code",
        )
        assert expected_line_item.asdict() == actual_line_items[0].asdict()

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.MercedesBenzUSAScraper._load_previous_day_line_items"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.execute_model_request"
    )
    def test__get_basic_line_when_basic_line_api_fails_then_return_previous_day_line_item(
        self, mock_execute_model_request, mock_load_previous_day_line_items
    ):
        mock_execute_model_request.return_value = []
        model = AvailableModel(
            "model_code", False, "/en/vehicles/build/c-class/cabriolet/c300a"
        )
        expected_line_item = create_test_line_item(vendor=Vendor.MERCEDES_BENZ)
        mock_load_previous_day_line_items.return_value = [expected_line_item]
        mock_session = Mock()
        mock_line_item_repository = Mock()

        scraper = MercedesBenzUSAScraper(
            line_item_repository=mock_line_item_repository,
            session=mock_session,
            config={},
        )
        actual_line_item = scraper._get_basic_line(model)

        mock_load_previous_day_line_items.assert_called_with(model)
        assert expected_line_item.asdict() == actual_line_item.asdict()

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.MercedesBenzUSAScraper._load_previous_day_line_items"
    )
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa.execute_model_request"
    )
    def test__get_basic_line_when_basic_line_api_fails_and_found_zero_previous_day_lines_items_then_return_none(
        self, mock_execute_model_request, mock_load_previous_day_line_items
    ):
        mock_execute_model_request.return_value = []
        model = AvailableModel(
            "model_code", False, "/en/vehicles/build/c-class/cabriolet/c300a"
        )
        mock_load_previous_day_line_items.return_value = []
        mock_session = Mock()
        mock_line_item_repository = Mock()

        scraper = MercedesBenzUSAScraper(
            line_item_repository=mock_line_item_repository,
            session=mock_session,
            config={},
        )
        actual_line_item = scraper._get_basic_line(model)

        mock_load_previous_day_line_items.assert_called_with(model)
        assert actual_line_item == []

    # TEST DATA -----------------------------------------------------------------------------------------------------------
    line_item = LineItem(
        recorded_at=today_dashed_str_with_key(),
        vendor=Vendor.MERCEDES_BENZ,
        series="C-Class",
        model_range_code="c300a",
        model_code="205483",
        line_code="DX0",
        line_description="Premium trim",
        model_description="C 300 Cabriolet",
        model_range_description="C-Class Convertible",
        line_option_codes=[],
        currency="USD",
        net_list_price=57250.0,
        gross_list_price=0.0,
        market=Market.US,
    )

    line_item2 = LineItem(
        recorded_at=today_dashed_str_with_key(),
        vendor=Vendor.MERCEDES_BENZ,
        series="C-Class",
        model_range_code="c300a",
        model_code="205483",
        line_code="DX02",
        line_description="Premium trim 2",
        model_description="C 300 Cabriolet",
        model_range_description="C-Class Convertible",
        line_option_codes=[],
        currency="USD",
        net_list_price=57250.0,
        gross_list_price=0.0,
        market=Market.US,
    )

    line_item_list = [
        LineItem(
            recorded_at=today_dashed_str_with_key(),
            vendor=Vendor.MERCEDES_BENZ,
            series="C-Class",
            model_range_code="c300a",
            model_code="205483",
            line_code="DX02",
            line_description="Premium trim 2",
            model_description="C 300 Cabriolet",
            model_range_description="C-Class Convertible",
            line_option_codes=[],
            currency="USD",
            net_list_price=57250.0,
            gross_list_price=0.0,
            market=Market.US,
        )
    ]

    model_no_line = AvailableModel(
        "model_code", False, "/en/vehicles/build/c-class/cabriolet/c300a"
    )

    model_with_line = AvailableModel(
        "model_code", True, "/en/vehicles/build/c-class/cabriolet/c300a"
    )
