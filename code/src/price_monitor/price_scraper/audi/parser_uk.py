from bs4 import BeautifulSoup
from loguru import logger

from src.price_monitor.model.vendor import Vendor

AUDI_VENDOR = Vendor.AUDI


def parse_available_model_range_links(model_homepage: str) -> list:
    html_parser = BeautifulSoup(model_homepage, "html.parser")
    model_links = []

    for audi_car_model in html_parser.find_all("audi-modelfinder-car-model"):
        try:
            car_link = (
                audi_car_model.findChild("a", class_="audi-button")
                .get("href")
                .split("/")
            )
            model_links.append(car_link[-2] + "/" + car_link[-1][:-5])
        except AttributeError as e:
            logger.error(
                f"[Audi-US] Unable to parse car_link, for car_model {audi_car_model}, {e}"
            )
            raise e
    return model_links
