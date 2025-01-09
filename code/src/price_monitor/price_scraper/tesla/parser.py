import json
import re
from typing import Dict, List, Optional, Set

from bs4 import BeautifulSoup
from loguru import logger

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor, compute_net_list_price
from src.price_monitor.price_scraper.constants import (
    GROSS_LIST_PRICE_FOR_US,
    MISSING_LINE_OPTION_DETAILS,
    NOT_AVAILABLE,
)
from src.price_monitor.price_scraper.tesla.constants import MODELS
from src.price_monitor.utils.clock import today_dashed_str
from src.price_monitor.utils.line_item_factory import (
    create_line_item,
    create_line_item_option_code,
)
from src.price_monitor.utils.utils import remove_new_line_characters

SKIP_TYPES = [
    "TRIM",
    "MODEL",
    "DRIVE_MODE",
    None,
    "WINTER_TIRES",
    "WINTER_WHEELS_C_GROUP",
]


def parse_line_items(model_page: str, market: Market) -> List[LineItem]:
    line_option_for_model: list
    tesla_object = _get_tesla_object(model_page)
    dss_services = tesla_object["DSServices"]
    lexicon_config_key = dss_services["KeyManager"]["keys"]["Lexicon"][0]["key"]
    lexicon = dss_services[lexicon_config_key]

    series = lexicon["product"]
    model_range = series
    model_range_code = series
    options = lexicon["options"]
    groups = lexicon["groups"]
    sku = lexicon["sku"]

    trim_codes = set()
    response = []

    for group in groups:
        # get the trim line codes for the model.
        if group["code"] == "TRIM":
            trim_code = group["options"]
            trim_codes.update(trim_code)
            logger.trace(f"Added trim codes for {model_range}: {trim_code}")

        # fetching the base model details
        if group["code"] == "MODEL":
            base_model_options = options[group["options"][0]]
            model_range = base_model_options["name"]
            model_range_code = base_model_options["code"]

    for trim_code in trim_codes:
        if "configurator" in sku["trims"][trim_code]:
            line_option_for_model = parse_available_options_for_model(
                market, groups, sku, options, trim_code
            )
            item = _create_line_item_from_trim(
                series=series,
                market=market,
                model_range=model_range,
                model_range_code=model_range_code,
                trim_code=trim_code,
                options=options,
                line_option=line_option_for_model,
            )
            if item:
                response.append(item)

    logger.trace(
        f"Parsed {len(trim_codes)} trims from for {model_range} from tesla object: {tesla_object}"
    )

    return response


def parse_available_models_links(page_headers: dict) -> Set[str]:
    model_links: Set[str] = set()

    for item in page_headers["centerLinks"][0]["panel"]["products"]:
        if item["title"].startswith("Model"):
            model_links.add(item["links"][1]["href"])

    logger.trace(f"Found {len(model_links)} models")
    return model_links


def parse_available_options_for_model(
    market: Market, groups: dict, sku: dict, options: dict, trim_code: str
) -> list[LineItemOptionCode]:
    line_option_for_model: list[LineItemOptionCode] = list()
    option_code: str
    option_type: str
    option_price: int
    option_inclusion: bool
    option_codes = _get_line_option_codes(sku, trim_code)
    for code in option_codes:
        if code in options:
            option_code = code
            option_type = _get_line_option_type(groups, option_code)
            # check for the invalid option type
            if option_type not in SKIP_TYPES:
                # check for availability of description
                if "name" not in options[code]:
                    option_description = MISSING_LINE_OPTION_DETAILS
                else:
                    option_description = str(options[code]["name"])
                option_price = _get_validated_line_option_price(option_code, options)
                if option_price is not None:
                    option_inclusion = _get_line_option_inclusion(option_price)
                    line_option_for_model.append(
                        create_line_item_option_code(
                            code=option_code,
                            type=option_type,
                            description=remove_new_line_characters(option_description),
                            net_list_price=compute_net_list_price(market, option_price),
                            gross_list_price=option_price,
                            included=option_inclusion,
                        )
                    )
    return line_option_for_model


def _get_validated_line_option_price(option_code, options):
    if "price" in options[option_code]:
        return options[option_code]["price"]
    return None


# the defaults have a price 0, hence the rest are considered as extra options
def _get_line_option_inclusion(option_price) -> bool:
    if option_price == 0:
        return True
    return False


def _get_line_option_codes(sku, trim_code) -> set[str]:
    option_codes: set[str] = set()
    # to extract the default option codes for the trim line.
    for code in sku["trims"][trim_code]["configurator"][0]["base_options"]:
        option_codes.add(code)

    # to extract the available options for the trim line.
    combinations = sku["trims"][trim_code]["configurator"][0]["combinations"]
    for combination in combinations:
        for i in range(len(combination)):
            option_codes.add(combination[i])

    # to extract the available accessories for the trim line.
    optional = sku["trims"][trim_code]["configurator"][0]["optional"]
    for option in optional:
        for i in range(len(option)):
            option_codes.add(option[i])
    return option_codes


def _get_line_option_type(groups, option_code) -> str:
    for i in range(len(groups)):
        if option_code in groups[i]["options"]:
            return str(groups[i]["code"])
    return MISSING_LINE_OPTION_DETAILS


def _create_line_item_from_trim(
    series: str,
    market: Market,
    model_range: str,
    model_range_code: str,
    trim_code: str,
    options: dict,
    line_option: list,
) -> Optional[LineItem]:
    trim = options[trim_code]

    if "pricing" not in trim:
        return None

    gross_list_price = 0
    currency = ""

    # extract gross_list_price and currency
    for price in trim["pricing"]:
        if price["type"] == "base_plus_trim":
            gross_list_price = price["value"]
            currency = price["context"]

    # Some trims are don't have a price equal to zero
    if gross_list_price == 0:
        return None

    gross_list_price = _add_extra_price_for_trim_line(gross_list_price, options, trim)
    net_list_price: float = compute_net_list_price(market, gross_list_price)

    if market == Market.US:
        gross_list_price = GROSS_LIST_PRICE_FOR_US

    line_description: str = trim["description"]

    line_description = get_line_description(line_description)

    return create_line_item(
        date=today_dashed_str(),
        vendor=Vendor.TESLA,
        series=series,
        model_range_code=model_range_code,
        model_range_description=model_range,
        model_code=trim["code"],
        model_description=model_range,
        line_code=trim["code"],
        line_description=line_description,
        currency=currency,
        line_option_codes=line_option,
        net_list_price=net_list_price,
        gross_list_price=gross_list_price,
        market=market,
        engine_performance_kw=NOT_AVAILABLE,
    )


def get_line_description(line_description: str) -> str:
    for constant_model in MODELS:
        line_description = line_description.replace("\xa0", " ")
        if constant_model in line_description:
            line_description = line_description.split(constant_model)[1]
            break
    return line_description.strip()


# update gross_list_price with the extra price for the trim line.
def _add_extra_price_for_trim_line(gross_list_price, options, trim) -> float:
    options_to_add = set()
    for extra_pricing in trim["extra_content"]:
        if extra_pricing["type"] == "base_plus_trim_pricing":
            for item in extra_pricing["content"]:
                if "options" in item:
                    options_to_add.update(item["options"])
    for item in options_to_add:
        gross_list_price += options[item]["price"]
    return gross_list_price


# extract json from the html page of the model.
def _get_tesla_object(model_page: str) -> Dict:
    html_parser = BeautifulSoup(model_page, "html.parser")
    tesla_object_pattern = re.compile(r"const dataJson = {(.*)(\s*)(.*)}", re.MULTILINE)

    for script in html_parser.find_all("script", {"src": False}):
        if script:
            match = tesla_object_pattern.search(script.getText())
            if match:
                try:
                    json_str = "{" + match.group(3) + "}}"
                    return json.loads(json_str)
                except Exception as e:
                    logger.error("Could not parse tesla object", e)
                    raise e
    return {}


def parse_model_and_series(model, market):
    if market == Market.US:
        model = model.split("/")[1]
    else:
        model = model.split("/")[2]
    series = model[0] + model[5]
    return model, series


def adjust_otr_price(line_items: LineItem, otr_prices):
    for line_item in line_items:
        line_item.on_the_road_price = parse_otr_price(
            otr_prices.get(line_item.line_code, "£0")
        )
    return line_items


def parse_otr_price(price_str: str):
    return float(price_str[1:].replace(",", ""))
