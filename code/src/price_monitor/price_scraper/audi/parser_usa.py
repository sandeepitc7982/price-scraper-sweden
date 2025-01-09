from bs4 import BeautifulSoup
from loguru import logger

from src.price_monitor.model.vendor import Vendor

AUDI_VENDOR = Vendor.AUDI


def parse_available_model_range_links(model_homepage: str) -> tuple[list, list]:
    html_parser = BeautifulSoup(model_homepage, "html.parser")
    links_having_price, links_not_having_price = [], []

    for audi_car_model in html_parser.find_all("audi-modelfinder-car-model"):
        has_price = (
            len(
                audi_car_model.findChildren(
                    "p", class_="audi-copy-s audi-modelfinder__car-model-price"
                )
            )
            != 0
        )
        try:
            car_link = audi_car_model.findChild("a", class_="audi-button").get("href")[
                :-5
            ]
            if has_price:
                links_having_price.append(car_link)
            else:
                links_not_having_price.append(car_link)
        except AttributeError as e:
            logger.error(
                f"[Audi-US] Unable to parse car_link, for car_model {audi_car_model}, {e}"
            )
            raise e
    return links_having_price, links_not_having_price
