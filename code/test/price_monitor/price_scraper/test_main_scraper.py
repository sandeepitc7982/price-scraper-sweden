import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from test.price_monitor.utils.test_data_builder import create_test_line_item
from unittest.mock import Mock, call, patch

from src.price_monitor.bootstrap import initialize
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.audi.scraper import AudiScraper
from src.price_monitor.price_scraper.bmw.scraper import BMWScraper
from src.price_monitor.price_scraper.main_scraper import (
    _init_scrapers,
    _start_scraper_jobs,
    scrape,
)
from src.price_monitor.price_scraper.tesla.scraper import TeslaScraper
from src.price_monitor.price_scraper.vendor_scraper import VendorScraper

line_item = create_test_line_item()


@patch.object(target=ThreadPoolExecutor, attribute="submit")
def test_scrape_saves_scraped_line_items(mock_thread_pool):
    line_item_repository_mock = Mock()
    line_item_repository_mock.load.return_value = []

    mock_job = Mock()
    mock_thread_pool.return_value = mock_job
    mock_job.result.return_value = [line_item]

    config = {
        "output": {"directory": "", "prices_filename": ""},
        "scraper": {"enabled": {"audi": ["DE"]}},
    }

    scrape(config, line_item_repository_mock)

    line_item_repository_mock.save.assert_has_calls([call([line_item])])


@patch("src.price_monitor.price_scraper.main_scraper._run_scraper")
def test_start_scraper_jobs_calls_run_scraper_for_each_scraper(mock_run_scraper):
    mock_run_scraper.return_value = [line_item]
    scraper_mock = Mock()

    actual = _start_scraper_jobs([scraper_mock])
    assert actual == [line_item]


def test_init_scraper_with_bmw_config_returns_bmw_scraper_with_countries_to_scrape():
    line_item_repository = ()
    scrapers_config = {"scraper": {"enabled": {Vendor.BMW: [Market.DE]}}}

    scrapers: list[VendorScraper] = _init_scrapers(
        scrapers_config, line_item_repository
    )

    for scraper in scrapers:
        assert isinstance(scraper, BMWScraper)
        assert scrapers[0].get_markets_to_scrape() == [Market.DE]


def test_init_scraper_with_audi_config_returns_audi_scraper():
    line_item_repository = ()
    scrapers_config = {"scraper": {"enabled": {Vendor.AUDI: [Market.US]}}}

    scrapers: list[VendorScraper] = _init_scrapers(
        scrapers_config, line_item_repository
    )

    for scraper in scrapers:
        assert isinstance(scraper, AudiScraper)
        assert scrapers[0].get_markets_to_scrape() == [Market.US]


def test_init_scraper_with_tesla_config_returns_tesla_scraper():
    line_item_repository = ()
    scrapers_config = {"scraper": {"enabled": {Vendor.TESLA: [Market.NL]}}}

    scrapers = _init_scrapers(scrapers_config, line_item_repository)

    for scraper in scrapers:
        assert isinstance(scraper, TeslaScraper)
        assert scrapers[0].get_markets_to_scrape() == [Market.NL]


def test_init_scraper_with_invalid_vendor_returns_no_scraper():
    line_item_repository = ()
    scrapers_config = {"scraper": {"enabled": {"invalid vendor": [Market.NL]}}}

    scrapers = _init_scrapers(scrapers_config, line_item_repository)

    assert scrapers == []


def test_init_config_sets_the_market_configuration_for_the_scrapers():
    expected = {
        "environment": "Staging",
        "output": {
            "directory": "data/",
            "prices_filename": "prices",
            "differences_filename": "changelog",
            "file_type": "dual",
        },
        "scraper": {
            "enabled": {
                "tesla": ["NL"],
            }
        },
        "notification": {
            "channels": {
                "gchat": {
                    "gchat_url": "SECRET::projects/375378227731/secrets/stg_gchat_url/versions/latest"
                },
                "teams": {
                    "teams_webhook": "SECRET::projects/375378227731/secrets/prod_teams_webhook/versions/latest"
                },
            },
            "urls": {
                "dashboard_url": "https://lookerstudio.google.com/u/0/reporting/9a5e84e7-f150-41ed-a071-9271e13ea4ca"
                "/page/bat4C"
            },
        },
        "feature_toggle": {
            "is_audi_enabled_for_US": True,
            "is_type_hierarchy_enabled_MB": True,
        },
    }

    with open(f"{Path(__file__).parent}/config.json", "w") as f:
        json.dump(expected, f)

    actual, adls = initialize(
        config_file=f"{Path(__file__).parent}/config.json",
        scraper="tesla",
        market="NL",
    )

    os.remove(f"{Path(__file__).parent}/config.json")

    assert actual == expected


@patch("src.price_monitor.price_scraper.main_scraper._start_scraper_jobs")
def test_scrape_when_some_line_items_are_already_present_then_repository_should_update_with_latest_scraped_data(
    mock_scraper_jobs,
):
    line_item_repository_mock = Mock()
    line_item_repository_mock.load.return_value = [
        create_test_line_item(vendor=Vendor.BMW)
    ]

    config = {
        "output": {"directory": "", "prices_filename": ""},
        "scraper": {"enabled": {"audi": ["DE"]}},
    }
    mock_scraper_jobs.return_value = [create_test_line_item(vendor=Vendor.AUDI)]

    scrape(config, line_item_repository_mock)

    line_item_repository_mock.update_line_items.assert_called_with(
        [create_test_line_item(vendor=Vendor.BMW)],
        [create_test_line_item(vendor=Vendor.AUDI)],
        config,
    )
