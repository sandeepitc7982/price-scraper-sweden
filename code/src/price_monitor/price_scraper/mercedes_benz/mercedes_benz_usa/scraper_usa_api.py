import requests
from loguru import logger

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.mercedes_benz.constants import BASE_URL_USA
from src.price_monitor.utils.caller import execute_request


def execute_all_models_request(session):
    url = "https://www.mbusa.com/content/public-api/vd/active-models?country=us&lang=en"
    return _execute_request_with_logs(url, session)


def execute_model_request(path: str, session):
    url = f"{BASE_URL_USA}{path}"
    return _execute_request_with_logs(url, session)


def _execute_request_with_logs(url: str, session: requests.Session):
    try:
        response = execute_request(
            method="get", url=url, session=session, response_format="text"
        )
        if len(response) == 0:
            logger.error(
                f"[{Vendor.MERCEDES_BENZ}-{Market.US}] Returned empty list of lines for {url}"
            )
        return response
    except Exception as e:
        logger.error(
            f"[{Vendor.MERCEDES_BENZ}-{Market.US}] Unable to fetch model/line details for {url}",
            e,
        )
