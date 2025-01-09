import time

import requests
from retry import retry

from src.price_monitor.price_scraper.constants import (
    DELAY_REQUEST_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
)


@retry(tries=3, delay=1, backoff=2)
def execute_request(
    method: str,
    url: str,
    session=None,
    headers=dict(),
    body=None,
    response_format="json",
    delay=DELAY_REQUEST_SECONDS,
    timeout=REQUEST_TIMEOUT_SECONDS,
):
    """Calls the request with the appropriate headers and stuff"""

    if session is None:
        session = requests.Session()

    headers["user-agent"] = USER_AGENT
    time.sleep(delay)

    if method == "get":
        response = session.get(url, params=body, headers=headers, timeout=timeout)
    elif method == "post":
        response = session.post(url, headers=headers, json=body, timeout=timeout)
    elif method == "put":
        response = session.put(url, headers=headers, data=body, timeout=timeout)
    elif method == "delete":
        response = session.delete(url, headers=headers)

    response.raise_for_status()

    if response_format == "json":
        return response.json()

    if response_format == "text":
        return response.text
