from concurrent.futures import Future, ThreadPoolExecutor

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.vendor import Market


class VendorScraper:
    def __init__(self, line_item_repository, config):
        self.markets = None
        self.line_item_repository = (line_item_repository,)
        self.config = config

    def get_markets_to_scrape(self) -> list[Market]:
        return self.markets

    def run(self):
        line_items_all_markets: list[LineItem] = []

        if len(self.get_markets_to_scrape()) > 0:
            scraper_market_jobs: list[Future] = []

            with ThreadPoolExecutor(
                thread_name_prefix="scraper",
                max_workers=len(self.get_markets_to_scrape()),
            ) as ex:
                for market in self.get_markets_to_scrape():
                    scraper = self.__class__(
                        self.line_item_repository,
                        self.config,
                    )
                    job_scrape_market = ex.submit(scraper.scrape_models, market)
                    scraper_market_jobs.append(job_scrape_market)

            for job in scraper_market_jobs:
                line_item = job.result()
                if line_item is not None:
                    line_items_all_markets.extend(line_item)
        return line_items_all_markets

    def scrape_models(self, market: Market) -> list[LineItem]:
        pass

    def run_tesla(self):
        pass
