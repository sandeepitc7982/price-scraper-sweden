import unittest
from unittest.mock import call, patch

from src.price_monitor.utils.selenium_caller import selenium_execute_request


class TestSeleniumCaller(unittest.TestCase):
    @patch("src.price_monitor.utils.selenium_caller.webdriver")
    def test_selenium_execute_request(self, mock_driver):
        expected_outcome = "This is a text"
        mock_driver.Chrome().page_source = expected_outcome

        actual_outcome = selenium_execute_request(url="url", response_format="text")

        assert actual_outcome == expected_outcome

    @patch("src.price_monitor.utils.selenium_caller.webdriver")
    def test_selenium_execute_request_with_json_response(self, mock_driver):
        expected_outcome = {"model": "I am Model"}
        model_page = '<html><head><meta name="color-scheme" content="light dark"><meta charset="utf-8"></head><body><pre>{"model":"I am Model"}</pre><div class="json-formatter-container"></div></body></html>'
        mock_driver.Chrome().page_source = model_page

        actual_outcome = selenium_execute_request(url="url", response_format="json")

        assert actual_outcome == expected_outcome

    @patch("src.price_monitor.utils.selenium_caller.Options")
    @patch("src.price_monitor.utils.selenium_caller.webdriver")
    def test_selenium_execute_request_should_call_with_headless(
        self, mock_driver, mock_options
    ):
        model_page = '<html><head><meta name="color-scheme" content="light dark"><meta charset="utf-8"></head><body><pre>{"model":"I am Model"}</pre><div class="json-formatter-container"></div></body></html>'
        mock_driver.Chrome().page_source = model_page
        selenium_execute_request(url="url", response_format="json")
        mock_options().add_argument.assert_has_calls(
            [call("--headless=new")], any_order=True
        )
