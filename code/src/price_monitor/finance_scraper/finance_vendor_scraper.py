from concurrent.futures import Future, ThreadPoolExecutor

from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.vendor import Market


class FinanceVendorScraper:
    def __init__(self, finance_line_item_repository, config):
        self.markets = None
        self.finance_line_item_repository = finance_line_item_repository
        self.config = config

    def get_markets_to_scrape(self) -> list[Market]:
        return self.markets

    def run(self):
        finance_line_items_all_markets: list[FinanceLineItem] = []

        if len(self.get_markets_to_scrape()) > 0:
            scraper_market_jobs: list[Future] = []

            with ThreadPoolExecutor(
                thread_name_prefix="finance_scraper",
                max_workers=len(self.get_markets_to_scrape()),
            ) as ex:
                for market in self.get_markets_to_scrape():
                    scraper = self.__class__(
                        self.finance_line_item_repository,
                        self.config,
                    )
                    job_scrape_market = ex.submit(
                        scraper.scrape_finance_options, market
                    )
                    scraper_market_jobs.append(job_scrape_market)

            for job in scraper_market_jobs:
                finance_line_item = job.result()
                if finance_line_item is not None:
                    finance_line_items_all_markets.extend(finance_line_item)
        return finance_line_items_all_markets

    def scrape_finance_options(self, market: Market) -> list[LineItem]:
        pass
