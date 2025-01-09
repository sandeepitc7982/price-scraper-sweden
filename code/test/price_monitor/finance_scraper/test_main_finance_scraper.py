import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from test.price_monitor.utils.test_data_builder import create_test_finance_line_item
from unittest.mock import Mock, call, patch

from src.price_monitor.bootstrap import initialize
from src.price_monitor.finance_scraper.audi.scraper import AudiFinanceScraper
from src.price_monitor.finance_scraper.main_finance_scraper import (
    _init_scrapers,
    _start_scraper_jobs,
    scrape_finance,
)
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.vendor_scraper import VendorScraper

finance_line_item = create_test_finance_line_item()


@patch.object(target=ThreadPoolExecutor, attribute="submit")
def test_scrape_saves_scraped_finance_line_items(mock_thread_pool):
    finance_line_item_repository_mock = Mock()
    finance_line_item_repository_mock.load.return_value = []

    mock_job = Mock()
    mock_thread_pool.return_value = mock_job
    mock_job.result.return_value = [finance_line_item]

    config = {
        "output": {"directory": "", "finance_option_filename": ""},
        "finance_scraper": {"enabled": {"audi": ["UK"]}},
    }

    scrape_finance(config, finance_line_item_repository_mock)

    finance_line_item_repository_mock.save.assert_has_calls([call([finance_line_item])])


@patch("src.price_monitor.finance_scraper.main_finance_scraper._run_finance_scraper")
def test_start_scraper_jobs_calls_run_scraper_for_each_scraper(mock_run_scraper):
    mock_run_scraper.return_value = [finance_line_item]
    scraper_mock = Mock()

    actual = _start_scraper_jobs([scraper_mock])
    assert actual == [finance_line_item]


def test_init_scraper_with_audi_config_returns_audi_scraper():
    line_item_repository = ()
    scrapers_config = {"finance_scraper": {"enabled": {Vendor.AUDI: [Market.UK]}}}

    scrapers: list[VendorScraper] = _init_scrapers(
        scrapers_config, line_item_repository
    )

    for scraper in scrapers:
        assert isinstance(scraper, AudiFinanceScraper)
        assert scrapers[0].get_markets_to_scrape() == [Market.UK]


def test_init_scraper_with_invalid_vendor_returns_no_scraper():
    line_item_repository = ()
    scrapers_config = {"finance_scraper": {"enabled": {"invalid vendor": [Market.NL]}}}
    scrapers = _init_scrapers(scrapers_config, line_item_repository)
    assert scrapers == []


def test_init_config_sets_the_market_configuration_for_the_scrapers():
    expected = {
        "adls": {"enabled": True},
        "environment": "Staging",
        "output": {
            "directory": "data/",
            "prices_filename": "prices",
            "finance_options_filename": "finance_options",
            "differences_filename": "changelog",
            "file_type": "dual",
        },
        "scraper": {
            "enabled": {
                "tesla": ["NL"],
            }
        },
        "finance_scraper": {
            "enabled": {
                "audi": ["UK"],
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
        finance_scraper="audi",
        market="UK",
    )

    os.remove(f"{Path(__file__).parent}/config.json")

    assert actual == expected


@patch("src.price_monitor.finance_scraper.main_finance_scraper._start_scraper_jobs")
def test_scrape_when_some_line_items_are_already_present_then_repository_should_update_with_latest_scraped_data(
    mock_scraper_jobs,
):
    finance_line_item_repository_mock = Mock()
    finance_line_item_repository_mock.load.return_value = [
        create_test_finance_line_item(vendor=Vendor.BMW)
    ]

    config = {
        "output": {"directory": "", "finance_options_filename": ""},
        "finance_scraper": {"enabled": {"audi": ["UK"]}},
    }
    mock_scraper_jobs.return_value = [create_test_finance_line_item(vendor=Vendor.AUDI)]

    scrape_finance(config, finance_line_item_repository_mock)

    finance_line_item_repository_mock.update_finance_line_item.assert_called_with(
        [create_test_finance_line_item(vendor=Vendor.BMW)],
        [create_test_finance_line_item(vendor=Vendor.AUDI)],
        config,
    )
