import unittest
from unittest.mock import Mock, call, patch

from src.price_monitor.finance_scraper.tesla.selenium import (
    get_finance_details_for_model,
)


class TestSeleniumCaller(unittest.TestCase):
    @patch("src.price_monitor.finance_scraper.tesla.selenium.WebDriverWait")
    @patch("src.price_monitor.finance_scraper.tesla.selenium.time")
    @patch("src.price_monitor.finance_scraper.tesla.selenium.Options")
    @patch("src.price_monitor.finance_scraper.tesla.selenium.webdriver")
    def test_get_finance_details_for_model_should_call_with_headless(
        self, mock_driver, mock_options, mock_time, mock_web_driver_wait
    ):
        model_page = '<html><head><meta name="color-scheme" content="light dark"><meta charset="utf-8"></head><body><pre>{"model":"I am Model"}</pre><div class="json-formatter-container"></div></body></html>'
        driver_mock = Mock()
        mock_driver.Chrome.return_value = driver_mock
        mock_web_driver_wait.Chrome.return_value = Mock()
        mock_driver.Chrome().page_source = model_page
        mock_variant = Mock()
        driver_mock.find_elements.return_value = [mock_variant]
        mock_variant.get_attribute.return_value = "MDL3"
        get_finance_details_for_model(url="url")
        mock_options().add_argument.assert_has_calls(
            [call("--headless=new")], any_order=True
        )
