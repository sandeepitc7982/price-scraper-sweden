from test.price_monitor.utils.test_data_builder import create_test_finance_line_item
from unittest.mock import patch

from src.price_monitor.finance_scraper.finance_vendor_scraper import (
    FinanceVendorScraper,
)
from src.price_monitor.model.vendor import Market

finance_line_item_de = create_test_finance_line_item(market=Market.DE)

finance_line_item_nl = create_test_finance_line_item(market=Market.NL)


def side_effect_scrape_models(market: Market):
    if market == Market.DE:
        return [finance_line_item_de]
    elif market == Market.NL:
        return [finance_line_item_nl]


@patch(
    "src.price_monitor.finance_scraper.finance_vendor_scraper.FinanceVendorScraper.scrape_finance_options"
)
def test_run_calls_scrape_finance_options_and_returns_collated_data(
    mock_scrape_finance_options,
):
    mock_scrape_finance_options.side_effect = side_effect_scrape_models

    scraper = FinanceVendorScraper(None, None)
    setattr(scraper, "markets", ["DE", "NL"])
    actual = scraper.run()

    assert actual == [finance_line_item_de, finance_line_item_nl]


@patch(
    "src.price_monitor.finance_scraper.finance_vendor_scraper.FinanceVendorScraper.scrape_finance_options"
)
def test_run_calls_scrape_finance_options_to_len_of_markets_given(
    mock_scrape_models,
):
    mock_scrape_models.side_effect = side_effect_scrape_models

    scraper = FinanceVendorScraper(None, None)
    setattr(scraper, "markets", ["DE", "NL"])
    actual = scraper.run()

    assert actual == [finance_line_item_de, finance_line_item_nl]
    assert 2 == mock_scrape_models.call_count
