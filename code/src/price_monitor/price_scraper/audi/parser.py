import re

from bs4 import BeautifulSoup

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor, compute_net_list_price
from src.price_monitor.price_scraper.audi.constants import (
    COMMON_OPTION_TYPE,
    DEAD_OPTION_STATUS,
    DEAD_OPTION_TYPE,
    INCLUDED_OPTION_STATUS,
)
from src.price_monitor.price_scraper.constants import (
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


def parse_available_model_links(model_homepage: str) -> tuple[list, list]:
    html_parser = BeautifulSoup(model_homepage, "html.parser")
    cars = html_parser.find_all("div", {"data-carlineid": re.compile(".*")})
    links_having_price, links_not_having_price = [], []
    for car in cars:
        has_price = len(car.findChildren("p", {"data-testid": "price"})) != 0
        car_link = car.findChild("a", {"data-testid": "discoverButton"}).get("href")[
            :-5
        ]
        if has_price:
            links_having_price.append(car_link)
        else:
            links_not_having_price.append(car_link)
    return [links_having_price, links_not_having_price]


def parse_model_line_item(
    model_link: str,
    model_code,
    model_configuration: dict,
    market: Market,
) -> LineItem:
    series, model_range_code = model_link.split("/")[5:7]
    trim_line_description = "N/A"

    for attribute in model_configuration["configuration"]["stock-car-attrs"]["attrs"]:
        if "trimline" in attribute:
            trim_line_code = attribute.split(".")[1]
            trim_line_description = trim_line_code.upper()
    gross_list_price: float = model_configuration["configuration"]["prices"]["modelRaw"]
    net_list_price: float = compute_net_list_price(market, gross_list_price)

    otr_price_with_nonstandard_option = model_configuration["configuration"]["prices"][
        "rotrRaw"
    ]
    nonstandard_option_price = model_configuration["configuration"]["prices"][
        "optionsRaw"
    ]
    on_the_road_price: float = (
        otr_price_with_nonstandard_option - nonstandard_option_price
    )

    return create_line_item(
        date=today_dashed_str(),
        vendor=AUDI_VENDOR,
        series=series,
        model_range_code=model_range_code,
        model_range_description=model_configuration["configuration"]["carlineName"],
        model_code=model_code,
        model_description=model_configuration["configuration"]["description"],
        line_code=model_configuration["configuration"]["model"],
        line_description=trim_line_description,
        line_option_codes=[],
        currency=model_configuration["configuration"]["prices"]["total"].split(" ")[-1],
        net_list_price=net_list_price,
        gross_list_price=gross_list_price,
        on_the_road_price=on_the_road_price,
        market=market,
        engine_performance_kw=NOT_AVAILABLE,
        engine_performance_hp=NOT_AVAILABLE,
    )


def parse_line_item_options_for_trimline(
    trimline_details: dict, option_common_details: dict, market: Market
) -> list[LineItemOptionCode]:
    options = trimline_details["items"]
    line_option_codes = []
    for option_code, option in options.items():
        option_price = options.get(option_code, {}).get("priceValue", 0)
        if (
            option["status"] != DEAD_OPTION_STATUS
            and option.get("itemType", "").lower() not in DEAD_OPTION_TYPE
        ):
            included = False
            if option["status"] in INCLUDED_OPTION_STATUS:
                if option_price != 0:
                    included = False
                else:
                    included = True
            option_description = remove_new_line_characters(
                option_common_details.get(option_code, {}).get(
                    "name", MISSING_LINE_OPTION_DETAILS
                )
            )
            if option_code in option_description and option_price == 0:
                continue

            option_type = option.get("itemType", MISSING_LINE_OPTION_DETAILS)

            line_option_codes.append(
                create_line_item_option_code(
                    code=option_code,
                    description=option_description,
                    type=option_type,
                    included=included,
                    net_list_price=compute_net_list_price(market, option_price),
                    gross_list_price=option_price,
                )
            )
    return line_option_codes


def parse_options_type(options_details_json: dict) -> dict:
    options_type = {}
    for option in options_details_json["data"]["configuredCar"]["catalog"]["features"][
        "data"
    ]:
        options_type[option["pr3"]] = option["group"]["name"]
    return options_type


def replace_options_type(
    line_option_codes: list[LineItemOptionCode], options_types: dict
):
    for line_option_code in line_option_codes:
        line_option_code.type = options_types.get(
            line_option_code.code, line_option_code.type
        )

        if (
            line_option_code.type in COMMON_OPTION_TYPE
            and line_option_code.gross_list_price == 0
        ):
            line_option_code.included = True
