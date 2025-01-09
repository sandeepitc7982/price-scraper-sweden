import glob
import os
import pytest
from src.price_monitor.model.vendor import Market, Vendor
from test.price_monitor.e2e.e2e_test_constants import YESTERDAY_DIR, TODAY_DIR, DATA_DIR
from test.price_monitor.e2e.e2e_test_utils import (
    run_price_scraper_and_assert_successful,
    verify_output_files,
    run_compare_and_assert_successful,
    add_yesterday_price_data,
    remove_yesterday_price_data,
    run_data_quality_checks_and_assert_successful,
    run_finance_scraper_and_assert_successful,
)


def price_scraper_e2e_test(market: Market, vendor: Vendor) -> None:
    # Scrape today's prices
    run_price_scraper_and_assert_successful(market=market, vendor=vendor)
    verify_output_files(market=market, vendor=vendor, file_name="prices")

    # Run price comparison
    add_yesterday_price_data()
    run_compare_and_assert_successful()
    verify_output_files(market=market, vendor=vendor, file_name="changelog")
    remove_yesterday_price_data()


def finance_scraper_e2e_test(market: Market, vendor: Vendor) -> None:
    # Scrape today's finance prices
    run_finance_scraper_and_assert_successful(market=market, vendor=vendor)
    verify_output_files(market=market, vendor=vendor, file_name="finance_options")


@pytest.mark.cli
class TestCli:

    @pytest.fixture(scope="class", autouse=True)
    def setup(self):
        """
        Create necessary directories for sample data
        """

        os.makedirs(YESTERDAY_DIR, exist_ok=True)
        os.makedirs(TODAY_DIR, exist_ok=True)

        yield

        # Clear dir contents
        for file in glob.glob(f"{DATA_DIR}/*/*"):
            os.remove(file)

        # Clean up dirs
        if os.path.exists(TODAY_DIR):
            os.rmdir(TODAY_DIR)
        if os.path.exists(YESTERDAY_DIR):
            os.rmdir(YESTERDAY_DIR)

    @pytest.mark.tesla
    def test_tesla_german_market_price_scraper(self):
        market = Market.DE
        vendor = Vendor.TESLA

        price_scraper_e2e_test(market=market, vendor=vendor)

    @pytest.mark.tesla
    @pytest.mark.skip("Currently failing")
    def test_tesla_uk_market_price_scraper(self):
        market = Market.UK
        vendor = Vendor.TESLA

        price_scraper_e2e_test(market=market, vendor=vendor)

    @pytest.mark.tesla
    @pytest.mark.skip("Currently failing")
    def test_tesla_uk_market_finance_scraper(self):
        market = Market.UK
        vendor = Vendor.TESLA

        finance_scraper_e2e_test(market=market, vendor=vendor)

    @pytest.mark.bmw
    def test_bmw_german_market_price_scraper(self):
        market = Market.DE
        vendor = Vendor.BMW

        price_scraper_e2e_test(market=market, vendor=vendor)

    @pytest.mark.bmw
    def test_bmw_uk_market_price_scraper(self):
        market = Market.UK
        vendor = Vendor.BMW

        price_scraper_e2e_test(market=market, vendor=vendor)

    @pytest.mark.bmw
    def test_bmw_uk_market_finance_scraper(self):
        market = Market.UK
        vendor = Vendor.BMW

        finance_scraper_e2e_test(market=market, vendor=vendor)

    @pytest.mark.mercedes
    def test_mercedes_benz_german_market_price_scraper(self):
        market = Market.DE
        vendor = Vendor.MERCEDES_BENZ

        price_scraper_e2e_test(market=market, vendor=vendor)

    @pytest.mark.mercedes
    def test_mercedes_benz_uk_market_price_scraper(self):
        market = Market.UK
        vendor = Vendor.MERCEDES_BENZ

        price_scraper_e2e_test(market=market, vendor=vendor)

    @pytest.mark.audi
    def test_audi_uk_market_price_scraper(self):
        market = Market.UK
        vendor = Vendor.AUDI

        price_scraper_e2e_test(market=market, vendor=vendor)

    @pytest.mark.audi
    def test_audi_uk_market_finance_scraper(self):
        market = Market.UK
        vendor = Vendor.AUDI

        finance_scraper_e2e_test(market=market, vendor=vendor)

    # TODO: Fix audi scraper
    @pytest.mark.skip(reason="Audi scraper is currently broken")
    @pytest.mark.audi
    def test_audi_german_market_price_scraper(self):
        market = Market.DE
        vendor = Vendor.AUDI

        price_scraper_e2e_test(market=market, vendor=vendor)

    @pytest.mark.dq
    def test_data_quality_checks(self):
        run_data_quality_checks_and_assert_successful()
