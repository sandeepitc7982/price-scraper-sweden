import json
import re

from retry import retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from src.price_monitor.price_scraper.constants import USER_AGENT


@retry(tries=5, delay=3, backoff=2)
def selenium_execute_request(
    url: str,
    response_format="json",
):
    """Calls the request with the appropriate headers and stuff"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    driver = webdriver.Chrome(
        options=chrome_options, service=ChromeService(ChromeDriverManager().install())
    )
    driver.get(url=url)
    response = driver.page_source
    driver.close()
    if response_format == "json":
        response = re.sub(r"<html>.*<pre>", "", response)
        response = re.sub(r"</pre>.*</html>", "", response)
        return json.loads(str(response))
    if response_format == "text":
        return response
