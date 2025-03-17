import time

from retry import retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from src.price_monitor.price_scraper.constants import USER_AGENT


@retry(tries=3, delay=3, backoff=2)
def get_otr_prices_for_sweden_model(
    url: str,
):
    response = {}
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--log-level=1")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--enable-unsafe-swiftshader")

    driver = webdriver.Chrome(
        options=chrome_options, service=ChromeService(ChromeDriverManager().install())
    )
    # driver = webdriver.Chrome(
    #     options=chrome_options
    # )
    driver.maximize_window()
    driver.get(url=url)

    try:
        button = WebDriverWait(driver, 0).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "tds-modal-close"))
        )
        button.click()
    except Exception:
        pass

    try:
        button = WebDriverWait(driver, 0).until(
            ec.element_to_be_clickable(("id", "tsla-accept-cookie"))
        )
        button.click()
    except Exception:
        pass

    try:
        modal_close = WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "tds-icon-close"))
        )
        modal_close.click()
        time.sleep(5)
    except Exception:
        pass

    variants = WebDriverWait(driver, 5).until(
        ec.presence_of_all_elements_located(
            (By.CLASS_NAME, "group--options_block--container")
        )
    )
    
    for variant in variants:
        line_item_code = variant.get_attribute("data-id")
        variant.click()
        time.sleep(5)
        response[line_item_code] = get_otr_price_for_trimline(driver)

    driver.close()

    if len(response) == 0:
        raise Exception("Unable to Scrape OTR for Tesla UK")

    return response


def get_otr_price_for_trimline(driver):
    # Find the finance options dropdown and click it
    finance_dropdown = driver.find_element(By.NAME, "finance-options-dropdown-selector")
    driver.execute_script("arguments[0].scrollIntoView(true);", finance_dropdown)
    driver.execute_script("arguments[0].click();", finance_dropdown)

    # Pause for 5 seconds to allow the dropdown to fully load
    time.sleep(5)

    # Find the target element by its ID and scroll into view before clicking
    button = driver.find_element(By.ID, "cash")
    driver.execute_script("arguments[0].scrollIntoView(true);", button)
    driver.execute_script("arguments[0].click();", button)

    # Pause for 5 seconds after clicking
    time.sleep(5)

    footer = WebDriverWait(driver, 3).until(
        ec.visibility_of_element_located((By.CLASS_NAME, "tds-text--h3"))
    )
    
    otr = footer.text
    return otr
