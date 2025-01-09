from concurrent.futures import Future, ThreadPoolExecutor
from typing import List

from loguru import logger

from src.price_monitor.finance_scraper.audi.scraper import AudiFinanceScraper
from src.price_monitor.finance_scraper.bmw.scraper import BMWFinanceScraper
from src.price_monitor.finance_scraper.finance_vendor_scraper import (
    FinanceVendorScraper,
)
from src.price_monitor.finance_scraper.tesla.scraper import TeslaFinanceScraper
from src.price_monitor.model.finance_line_item import FinanceLineItem
from src.price_monitor.model.vendor import Vendor
from src.price_monitor.repository.finance_item_repository import (
    FileSystemFinanceLineItemRepository,
)
from src.price_monitor.utils.clock import today_dashed_str_with_key


def scrape_finance(
    config: dict,
    finance_line_item_repository: FileSystemFinanceLineItemRepository,
):
    scrapers = _init_scrapers(
        config=config,
        finance_line_item_repository=finance_line_item_repository,
    )
    scraped_finance_options = _start_scraper_jobs(scrapers=scrapers)
    existing_line_items = finance_line_item_repository.load(today_dashed_str_with_key())
    if len(existing_line_items) == 0:
        finance_line_item_repository.save(scraped_finance_options)
    else:
        finance_line_item_repository.update_finance_line_item(
            existing_line_items, scraped_finance_options, config
        )


def _init_scrapers(config: dict, finance_line_item_repository):
    scrapers_list = list()
    vendor_scraper_map = {
        Vendor.AUDI: AudiFinanceScraper,
        Vendor.BMW: BMWFinanceScraper,
        Vendor.TESLA: TeslaFinanceScraper,
    }

    for vendor in config["finance_scraper"]["enabled"]:
        if vendor in vendor_scraper_map.keys():
            scraper_vendor_instance = vendor_scraper_map[vendor](
                finance_line_item_repository, config
            )
            scrapers_list.append(scraper_vendor_instance)
    return scrapers_list


def _start_scraper_jobs(scrapers: list[FinanceVendorScraper]):
    scraper_jobs: List[Future] = []
    all_finance_options: List[FinanceLineItem] = []

    if len(scrapers) > 0:
        with ThreadPoolExecutor(
            thread_name_prefix="finance_scraper", max_workers=len(scrapers)
        ) as ex:
            for scraper_instance in scrapers:
                job = ex.submit(_run_finance_scraper, scraper_instance)
                scraper_jobs.append(job)

        for job in scraper_jobs:
            finance_line_item = job.result()

            if finance_line_item is not None:
                all_finance_options.extend(finance_line_item)

    return all_finance_options


def _run_finance_scraper(scraper: FinanceVendorScraper):
    try:
        logger.info(f"Running finance {scraper.__str__()} scraper...")
        return scraper.run()
    except Exception as e:
        logger.exception(f"Failed to process updates for {scraper.__str__()}", {e})
