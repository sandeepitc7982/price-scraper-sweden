from concurrent.futures import Future, ThreadPoolExecutor
from typing import List

from loguru import logger

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.vendor import Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.price_scraper.audi.scraper import AudiScraper
from src.price_monitor.price_scraper.bmw.scraper import BMWScraper
from src.price_monitor.price_scraper.mercedes_benz.scraper import MercedesBenzScraper
from src.price_monitor.price_scraper.tesla.scraper import TeslaScraper
from src.price_monitor.price_scraper.vendor_scraper import VendorScraper
from src.price_monitor.utils.clock import today_dashed_str_with_key


def scrape(
    config: dict,
    line_item_repository: FileSystemLineItemRepository,
):
    scrapers = _init_scrapers(
        config=config,
        line_item_repository=line_item_repository,
    )
    scraped_line_items = _start_scraper_jobs(scrapers=scrapers)
    existing_line_items = line_item_repository.load(today_dashed_str_with_key())
    if len(existing_line_items) == 0:
        line_item_repository.save(scraped_line_items)
    else:
        line_item_repository.update_line_items(
            existing_line_items, scraped_line_items, config
        )


def _init_scrapers(config: dict, line_item_repository) -> list[VendorScraper]:
    scrapers_list = list()
    vendor_scraper_map = {
        Vendor.AUDI: AudiScraper,
        Vendor.BMW: BMWScraper,
        Vendor.TESLA: TeslaScraper,
        Vendor.MERCEDES_BENZ: MercedesBenzScraper,
    }

    for vendor in config["scraper"]["enabled"]:
        if vendor in vendor_scraper_map.keys():
            scraper_vendor_instance = vendor_scraper_map[vendor](
                line_item_repository, config
            )
            scrapers_list.append(scraper_vendor_instance)
    return scrapers_list


def _start_scraper_jobs(scrapers: list[VendorScraper]):
    scraper_jobs: List[Future] = []
    all_line_items: List[LineItem] = []

    if len(scrapers) > 0:
        with ThreadPoolExecutor(
            thread_name_prefix="scraper", max_workers=len(scrapers)
        ) as ex:
            for scraper_instance in scrapers:
                job = ex.submit(_run_scraper, scraper_instance)
                scraper_jobs.append(job)

        for job in scraper_jobs:
            line_item = job.result()
            if line_item is not None:
                all_line_items.extend(line_item)

        logger.info(f"Saving {len(all_line_items)} line items to disk")
    return all_line_items


def _run_scraper(scraper: VendorScraper):
    try:
        if scraper.__class__ == TeslaScraper:
            return scraper.run_tesla()
        else:
            logger.info(f"Running {scraper.__str__()} scraper...")
            return scraper.run()
    except Exception as e:
        logger.exception(f"Failed to process updates for {scraper.__str__()}", {e})
