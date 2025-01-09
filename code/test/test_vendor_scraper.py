from test.price_monitor.utils.test_data_builder import create_test_line_item
from unittest.mock import patch

from src.price_monitor.model.vendor import Market
from src.price_monitor.price_scraper.vendor_scraper import VendorScraper

line_item_de = create_test_line_item(market=Market.DE)

line_item_nl = create_test_line_item(market=Market.NL)


def side_effect_scrape_models(market: Market):
    if market == Market.DE:
        return [line_item_de]
    elif market == Market.NL:
        return [line_item_nl]


@patch("src.price_monitor.price_scraper.vendor_scraper.VendorScraper.scrape_models")
def test_run_calls_scrape_models_and_returns_collated_data(
    mock_scrape_models,
):
    mock_scrape_models.side_effect = side_effect_scrape_models

    scraper = VendorScraper(None, None)
    setattr(scraper, "markets", ["DE", "NL"])
    actual = scraper.run()

    assert actual == [line_item_de, line_item_nl]


@patch("src.price_monitor.price_scraper.vendor_scraper.VendorScraper.scrape_models")
def test_run_calls_scrape_models_to_len_of_markets_given(
    mock_scrape_models,
):
    mock_scrape_models.side_effect = side_effect_scrape_models

    scraper = VendorScraper(None, None)
    setattr(scraper, "markets", ["DE", "NL"])
    actual = scraper.run()

    assert actual == [line_item_de, line_item_nl]
    assert 2 == mock_scrape_models.call_count
