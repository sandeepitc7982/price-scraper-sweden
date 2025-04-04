import time

from loguru import logger
from retry import retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from src.price_monitor.finance_scraper.tesla.constants import METALLIC_PAINT_CODE
from src.price_monitor.price_scraper.constants import USER_AGENT
from selenium.webdriver.support import expected_conditions as ec


@retry(tries=3, delay=3, backoff=2)
def get_finance_details_for_model(
    url: str,
):
    response = {}
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    driver = webdriver.Chrome(
        options=chrome_options, service=ChromeService(ChromeDriverManager().install())
    )
    driver.maximize_window()
    driver.get(url=url)

    try:
        button = driver.find_element(By.CLASS_NAME, "tds-modal-close")
        button.click()
    except Exception:
        pass

    try:
        button = driver.find_element("id", "tsla-accept-cookie")
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

    variants = driver.find_elements(By.CLASS_NAME, "group--options_block--container")
    for variant in variants:
        line_item_code = variant.get_attribute("data-id")
        variant.click()
        time.sleep(5)

        try:
            deep_blue_metallic_label = driver.find_element(
                By.XPATH, f"//label[@for='PAINT_{METALLIC_PAINT_CODE}']"
            )

            # Scroll the element into view
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", deep_blue_metallic_label
            )

            # Click the label directly using JavaScript
            driver.execute_script("arguments[0].click();", deep_blue_metallic_label)

        except Exception as e:
            logger.error(
                f"Error occurred while selecting lowest price metallic paint with code {METALLIC_PAINT_CODE}: {e}"
            )

        response[line_item_code] = get_finance_details_for_trimline(driver)
    driver.close()
    if len(response) == 0:
        raise "Unable to Scrape Finance Option for Tesla UK"
    return response


def get_finance_details_for_trimline(driver):
    downpayment = 4999

    # Locate the footer
    footer = driver.find_element(By.TAG_NAME, "footer")

    button = footer.find_element(By.TAG_NAME, "button")
    button.click()

    finance_options = {}

    finance_options["PCP"] = get_pcp_details(downpayment, driver)

    modal_close = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.CLASS_NAME, "tds-icon-close-filled"))
    )
    modal_close.click()

    return finance_options


def get_pcp_details(downpayment, driver):
    try:
        # Find the finance options dropdown and click it
        button = driver.find_element(By.NAME, "finance-options-dropdown-selector")
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        driver.execute_script("arguments[0].click();", button)

        # Pause for 5 seconds to allow the dropdown to fully load
        time.sleep(5)

        # Find the target element by its ID and scroll into view before clicking
        button = driver.find_element(
            By.ID, "private-finplat.AUTO_LOAN:BALLOON_LOAN:CT_PRIVATE"
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        driver.execute_script("arguments[0].click();", button)

        # Pause for 5 seconds after clicking
        time.sleep(5)

        downpayment_field = driver.find_element("id", "cashDownPayment")
        for _ in range(7):
            downpayment_field.send_keys(Keys.BACKSPACE)
        downpayment_field.send_keys(downpayment)

        # Wait for the dropdown to be clickable and then click to open it
        dropdown_button = WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, "button.tds-dropdown-trigger"))
        )
        dropdown_button.click()

        # Wait for the list of options to become visible and click the "48 Months" option
        option_48_months = WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable((By.XPATH, "//li[@data-tds-value='48']"))
        )
        option_48_months.click()

        rental_th = WebDriverWait(driver, 10).until(
            ec.visibility_of_element_located((By.CLASS_NAME, "price-tag"))
        )

        # Wait until the paragraph with the representative example is visible
        pcp_details_text = WebDriverWait(driver, 10).until(
            ec.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class, 'finance-modal-disclaimer')]//p[2]")
            )
        )
        pcp_details = {
            "rental_th": rental_th.text,
            "details": pcp_details_text.text,
        }
        return pcp_details
    except Exception as e:
        logger.error(f"Unable to fetch pcp price {e}")
