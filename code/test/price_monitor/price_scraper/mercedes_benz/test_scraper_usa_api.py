import unittest
from unittest.mock import Mock, patch

from requests import HTTPError

from src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa_api import (
    execute_all_models_request,
    execute_model_request,
)


class TestScarperUSAAPi(unittest.TestCase):
    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa_api.execute_request"
    )
    def test_execute_model_request_returns_none_when_it_fails(
        self,
        mock_execute_request,
    ):
        mock_session = Mock()
        mock_execute_request.side_effect = HTTPError()

        actual = execute_model_request("path", mock_session)

        assert actual is None

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa_api.execute_request"
    )
    def test_execute_model_request_returns_empty_list_when_response_is_empty(
        self, mock_execute_request
    ):
        mock_session = Mock()
        mock_execute_request.return_value = []

        actual = execute_model_request("path", mock_session)

        assert actual == []

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa_api.execute_request"
    )
    def test_execute_all_models_request_returns_none_when_it_fails(
        self,
        mock_execute_request,
    ):
        mock_session = Mock()
        mock_execute_request.side_effect = HTTPError()

        actual = execute_all_models_request(mock_session)

        assert actual is None

    @patch(
        "src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa_api.execute_request"
    )
    def test_execute_all_models_request_returns_empty_list_when_response_is_empty(
        self, mock_execute_request
    ):
        mock_session = Mock()
        mock_execute_request.return_value = []

        actual = execute_all_models_request(mock_session)

        assert actual == []
