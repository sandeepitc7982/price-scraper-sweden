from concurrent.futures import Future, ThreadPoolExecutor

import requests
from loguru import logger

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.price_scraper.bmw.constants import (
    USA_MODEL_CONFIGURATION_URL,
    USA_MODEL_LIST_URL,
)
from src.price_monitor.price_scraper.bmw.parser_usa import (
    extract_price,
    parse_all_available_options,
    parse_extra_designs_list,
    parse_is_option_constructible,
    parse_line_items,
    parse_model_code_list_from_json,
)
from src.price_monitor.price_scraper.constants import E2E_TEST_LIST_SIZE
from src.price_monitor.utils.caller import execute_request
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


def scrape_models_for_usa(
    line_item_repository: FileSystemLineItemRepository,
    config: dict,
    market: Market = Market.US,
):
    session = requests.Session()
    line_items = []

    model_list_json = execute_request("get", USA_MODEL_LIST_URL, session)

    model_code_list = parse_model_code_list_from_json(model_list_json)

    if config.get("e2e_tests"):
        model_code_list = list(model_code_list)[:E2E_TEST_LIST_SIZE]

    per_model_jobs: list[Future] = []
    with ThreadPoolExecutor(
        thread_name_prefix="scraper",
        max_workers=len(model_code_list),
    ) as ex:
        for model_code in model_code_list:
            try:
                model_details = get_model_details(model_code, session)
                job_for_a_model = ex.submit(
                    get_line_items_for_model,
                    market,
                    model_details,
                    session,
                    line_item_repository,
                )
                per_model_jobs.append(job_for_a_model)
            except Exception as e:
                logger.error(
                    f"[{market}] Failed to scrape model for {Vendor.BMW}, for model code : {model_code}. Reason : {e}, "
                    f"Loading previous data...."
                )
                list_of_line_item = (
                    line_item_repository.load_model_filter_by_model_code(
                        date=yesterday_dashed_str_with_key(),
                        market=market,
                        vendor=Vendor.BMW,
                        model_code=model_code,
                    )
                )
                if len(list_of_line_item) > 0:
                    line_items.extend(list_of_line_item)
                    logger.info(
                        f"[{market}] Loaded {len(list_of_line_item)} trim lines for model: "
                        f"{list_of_line_item[0].series} {list_of_line_item[0].model_range_description} "
                        f"{list_of_line_item[0].model_description} {list_of_line_item[0].line_description}"
                    )

    for job in per_model_jobs:
        if job.result() is not None:
            line_items.extend(job.result())

    logger.info(f"[US] Found {len(line_items)} line items")
    return line_items


def get_model_details(model_code, session):
    model_url = f"{USA_MODEL_CONFIGURATION_URL}/start/{model_code}"
    model_details = execute_request("get", model_url, session)
    return model_details


def get_line_items_for_model(market, model_details, session, line_item_repository):
    # Basic Session key, used for getting the constructability of the option for a line.
    model_key = model_details["cmId"]
    line_items = parse_line_items(model_details)
    for line_item in line_items:
        try:
            line_details = get_line_specific_details(
                model_details, line_item, model_key, session
            )
            if line_item.line_description != "BASIC_LINE":
                line_item.net_list_price = extract_price(line_details)
            _scrape_line_options(
                line_details,
                line_item,
                line_item_repository,
                market,
                model_details,
                model_key,
                session,
            )
        except Exception as e:
            logger.error(
                f"[{market}] Failed to scrape trim line for {Vendor.BMW}, for model:  {line_item.series} "
                f"{line_item.model_range_description} {line_item.model_description} {line_item.line_description}. "
                f"Reason: '{e}'. Loading options from previous dataset..."
            )
            list_of_line_item = line_item_repository.load_model_filter_by_trim_line(
                date=yesterday_dashed_str_with_key(),
                market=market,
                vendor=Vendor.BMW,
                model_code=line_item.model_code,
                line_code=line_item.line_code,
            )
            if len(list_of_line_item) > 0:
                line_item = list_of_line_item[0]
                logger.info(
                    f"[{market}] Loaded Trim Line for model: {line_item.series} {line_item.model_range_description} "
                    f"{line_item.model_description} {line_item.line_description}"
                )
            else:
                continue
    return line_items


def _scrape_line_options(
    line_details,
    line_item,
    line_item_repository,
    market,
    model_details,
    model_key,
    session,
):
    try:
        line_item.line_option_codes = get_line_options(
            line_details, model_details, model_key, session
        )
    except Exception as e:
        logger.error(
            f"[{market}] Failed to scrape options for {Vendor.BMW}, for model:  {line_item.series} "
            f"{line_item.model_range_description} {line_item.model_description} {line_item.line_description}. "
            f"Reason: '{e}'. Loading options from previous dataset..."
        )
        line_option_codes = line_item_repository.load_line_option_codes_for_line_code(
            date=yesterday_dashed_str_with_key(),
            market=market,
            vendor=Vendor.BMW,
            model_code=line_item.model_code,
            line_code=line_item.line_code,
        )
        if len(line_option_codes) > 0:
            line_item.line_option_codes = line_option_codes
            logger.info(
                f"[{market}] Loaded {len(line_item.line_option_codes)} Options for model: "
                f"{line_item.series} {line_item.model_range_description} {line_item.model_description} "
                f"{line_item.line_description}"
            )


def get_line_specific_details(
    model_details: dict, line_item: LineItem, model_key: str, session
):
    logger.debug(
        f"[{Market.US}] Fetching line options for {model_details['model']['series']}, "
        f"{model_details['model']['bodyStyle']}, {model_details['model']['name']} line {line_item.line_description}"
    )
    if line_item.line_code == "BASIC_LINE":
        return model_details
    url = f"{USA_MODEL_CONFIGURATION_URL}/{model_key}/{line_item.line_code}"
    line_details = execute_request("put", url, session)
    # BMW USA provides a base session, after checking the details with line, need to rollback it's to initial state.
    url = f"{USA_MODEL_CONFIGURATION_URL}/{model_key}/undo"
    execute_request("get", url, session)
    return line_details


def get_line_options(
    line_details: dict,
    model_details: dict,
    model_key: str,
    session,
) -> list:
    line_options = []
    extra_designs_list = parse_extra_designs_list(line_details)
    all_available_options = parse_all_available_options(
        line_details, model_details["optionDetails"]
    )
    for option in all_available_options:
        is_constructible = is_option_constructible_for_line(
            extra_designs_list, model_key, option, session
        )
        if is_constructible:
            line_options.append(option)
    return line_options


def is_option_constructible_for_line(
    extra_designs_list: list, model_key: str, option: LineItemOptionCode, session
) -> bool:
    url = f"{USA_MODEL_CONFIGURATION_URL}/{model_key}/{option.code}"
    options_constructability_json = execute_request("put", url, session)
    is_constructible = parse_is_option_constructible(
        extra_designs_list, options_constructability_json
    )
    try:
        undo_url = f"{USA_MODEL_CONFIGURATION_URL}/{model_key}/undo"
        execute_request("get", undo_url, session)
    except Exception:
        try:
            execute_request("delete", url, session)
        except Exception:
            logger.debug(
                f"[US] Unable to undo operation for model_key {model_key} for option {option.code}-{option.description}"
            )
    return is_constructible
