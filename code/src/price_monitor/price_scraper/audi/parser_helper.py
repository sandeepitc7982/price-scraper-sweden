import re
from typing import List

from loguru import logger

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import (
    Currency,
    Market,
    Vendor,
    compute_net_list_price,
)
from src.price_monitor.price_scraper.audi.constants import (
    DEAD_OPTION_STATUS,
    DEAD_OPTION_TYPE,
    INCLUDED_OPTION_STATUS,
)
from src.price_monitor.price_scraper.constants import (
    GROSS_LIST_PRICE_FOR_US,
    MISSING_LINE_OPTION_DETAILS,
    NOT_AVAILABLE,
)
from src.price_monitor.utils.clock import today_dashed_str
from src.price_monitor.utils.line_item_factory import (
    create_line_item,
    create_line_item_option_code,
)
from src.price_monitor.utils.utils import remove_new_line_characters

AUDI_VENDOR = Vendor.AUDI


def parse_model_line_item(
    model_configuration: dict, link: str, market: Market, model_details
) -> LineItem:
    series: str = ""
    trim_line_code: str = ""
    trim_line_description: str = "N/A"
    model_range_code: str = ""
    currency: str = ""
    net_list_price: float = 0.00
    gross_list_price: float = 0.00
    on_the_road_price: float = 0.0
    if market == Market.US:
        series, model_range_code = link.split("/")[5:7]
        currency = Currency.US
        # Currently, gross and net prices are the same for now. As we don't have proper tax info for US.
        net_list_price = model_configuration["configuration"]["prices"]["modelRaw"]
        gross_list_price = GROSS_LIST_PRICE_FOR_US
    if market == Market.UK:
        series, model_range_code = link.split("/")[:2]
        currency = Currency.UK
        gross_list_price = model_configuration["configuration"]["prices"]["modelRaw"]
        net_list_price = compute_net_list_price(market, gross_list_price)

        otr_price_with_nonstandard_option = model_configuration["configuration"][
            "prices"
        ]["rotrRaw"]
        nonstandard_option_price = model_configuration["configuration"]["prices"][
            "optionsRaw"
        ]
        on_the_road_price = otr_price_with_nonstandard_option - nonstandard_option_price

    model_range_description = model_configuration["configuration"].get(
        "carlineName", model_range_code
    )
    model_description = model_configuration["configuration"]["description"]

    for attribute in model_configuration["configuration"]["stock-car-attrs"]["attrs"]:
        # Condition to split the string based on availability of the term "model-range" in it.
        # Example: attribute = "model-range a6"
        if "trimline" in attribute:
            trim_line_code = attribute.split(".")[1]

        trim_line_description = trim_line_code.upper()
    model_code = model_configuration["configuration"]["model"]
    try:
        engine_performance_kw, engine_performance_hp = get_engine_performance(
            model_code, model_details
        )
    except Exception as e:
        logger.error(
            f"[{market}] Unable to fetch engine performance for {series}, {model_range_description}, {model_description}. Due to Reason {e}"
        )
        engine_performance_kw, engine_performance_hp = NOT_AVAILABLE, NOT_AVAILABLE

    return create_line_item(
        date=today_dashed_str(),
        vendor=AUDI_VENDOR,
        series=series,
        model_range_code=model_range_code,
        model_range_description=model_range_description,
        model_code=model_code,
        model_description=model_description,
        line_code=trim_line_code,
        line_description=trim_line_description,
        line_option_codes=[],
        currency=currency,
        net_list_price=net_list_price,
        gross_list_price=gross_list_price,
        on_the_road_price=on_the_road_price,
        market=market,
        engine_performance_kw=engine_performance_kw,
        engine_performance_hp=engine_performance_hp,
    )


def parse_line_option_codes(
    model_data, descriptions, option_types, market: Market
) -> List[LineItemOptionCode]:
    line_option_codes = []

    for code, option in model_data["items"].items():
        included = False
        model_raw_price = option.get("priceValue", 0)
        net_list_price = model_raw_price
        if market == Market.UK:
            net_list_price = compute_net_list_price(market, model_raw_price)

        if (
            option["status"] != DEAD_OPTION_STATUS
            and option.get("itemType", "").lower() not in DEAD_OPTION_TYPE
        ):
            if option["status"] in INCLUDED_OPTION_STATUS:
                if model_raw_price != 0 and option.get("itemType") != "model":
                    included = False
                else:
                    included = True

            option_type = MISSING_LINE_OPTION_DETAILS
            if (
                "family" in descriptions[code]
                and descriptions[code]["family"] in option_types
            ):
                if "group" in option_types[descriptions[code]["family"]]:
                    option_type = option_types[descriptions[code]["family"]]["group"]
                else:
                    option_type = option_types[descriptions[code]["family"]].get(
                        "type", MISSING_LINE_OPTION_DETAILS
                    )

            if option_type == MISSING_LINE_OPTION_DETAILS:
                option_type = option.get("itemType", MISSING_LINE_OPTION_DETAILS)
            option_description = remove_new_line_characters(
                descriptions.get(code, {}).get("name", MISSING_LINE_OPTION_DETAILS)
            )
            # Ignoring the options whose description doesn't contain any information, only containing option code itself.
            if code in option_description and model_raw_price == 0:
                continue

            line_option_codes.append(
                # Currently, gross and net prices are the same for now. As we don't have proper tax info for US.
                create_line_item_option_code(
                    code=code,
                    description=option_description,
                    type=option_type,
                    included=included,
                    net_list_price=net_list_price,
                    gross_list_price=model_raw_price,
                )
            )

    return line_option_codes


def get_engine_performance(model_code, model_details):
    engine_performance_kw = model_details[model_code].get("max-output-kw", "")
    engine_performance_hp = model_details[model_code].get("max-output-ps", "")
    ep_kw_str, ep_hp_str = parse_engine_performance_kw_and_hp(
        model_details[model_code].get("max-output", "")
    )
    if engine_performance_kw == "":
        engine_performance_kw = ep_kw_str
    if engine_performance_hp == "":
        engine_performance_hp = ep_hp_str
    return engine_performance_kw, engine_performance_hp


def parse_engine_performance_kw_and_hp(engine_performance) -> list[str:str]:
    try:
        if engine_performance == "":
            return [NOT_AVAILABLE, NOT_AVAILABLE]
        # Checking for 2 or 3 continuous digit formats
        pattern = r"(?<![,.])\b\d{2,3}[:PS|kW]*\b"
        matches = re.findall(pattern, engine_performance)
        # Sometimes we found only found 1. i.e, kW
        if len(matches) == 1:
            matches.append("100000")
        # Taking only first two occurence, because in case of Audi only those are valid
        matches = matches[:2]
        if "PS" in matches[0] or "kW" in matches[0]:
            matches[0] = matches[0][:-2]
        if "PS" in matches[1] or "kW" in matches[1]:
            matches[1] = matches[1][:-2]
        matches.sort(key=int)
        if matches[1] == "100000" or matches[1] == "":
            matches[1] = NOT_AVAILABLE
        return matches
    except Exception:
        return [NOT_AVAILABLE, NOT_AVAILABLE]
