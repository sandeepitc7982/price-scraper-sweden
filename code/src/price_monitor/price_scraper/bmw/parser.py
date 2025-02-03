import base64
import itertools
import json
import re
import urllib
from typing import List

from bs4 import BeautifulSoup
from loguru import logger

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import (
    LineItemOptionCode,
    create_default_line_item_option_code,
)
from src.price_monitor.model.vendor import (
    Currency,
    Market,
    Vendor,
    compute_net_list_price,
)
from src.price_monitor.price_scraper.bmw.constants import HP_UNIT, KW_UNIT, X_API_KEY, SWEDEN_G45_DESC
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

STANDARD_LINES = ["BASIC_LINE", "M_PERFORMANCE_LINE"]


def parse_model_matrix_to_line_items(
    model_matrix: dict, market: Market
) -> List[LineItem]:
    response: List[LineItem] = []

    # These are sometimes returned when the order and effect dates are not correct
    if "closestEffectDate" in model_matrix:
        del model_matrix["closestEffectDate"]
    if "closestOrderDate" in model_matrix:
        del model_matrix["closestOrderDate"]

    for series in model_matrix.values():
        response.extend(_parse_series_to_line_items(series, market))
    return response


def _parse_series_to_line_items(series: dict, market: Market) -> List[LineItem]:
    response: List[LineItem] = []

    for model_range in series["modelRanges"].values():
        response.extend(_parse_model_range_to_line_items(series, model_range, market))

    return response


def _parse_model_range_to_line_items(
    series: dict, model_range: dict, market: Market
) -> List[LineItem]:
    response: List[LineItem] = []
    for line_code, line in model_range["lines"].items():
        response.extend(
            _parse_line_to_line_items(series, model_range, line_code, line, market)
        )
    return response


def _parse_line_to_line_items(
    series: dict, model_range: dict, line_code: str, line: dict, market: Market
) -> List[LineItem]:
    response: List[LineItem] = []

    # For each model we are getting different transmission variants. Ex. mannual, auto. So, we are taking the model which has the lowest price among all the transmission variants.
    model_variants_group = itertools.groupby(
        line["includedTransmissionVariants"],
        key=lambda x: x["configuration"]["modelCode"],
    )
    for model in model_variants_group:
        variants = list(model[1])
        try:
            min_price_variant = min(variants, key=lambda x: x["prices"]["grossPrice"])
            response.append(
                _parse_transmission_variant_line_to_line_items(
                    series, model_range, line_code, line, min_price_variant, market
                )
            )
        except Exception as e:
            logger.error(
                f"Failed to find price for model with series {series['code']}, model range {model_range['code']}, line {line_code}, model {variants[0]['configuration']['modelCode']}, {e}"
            )

    return response


def _parse_transmission_variant_line_to_line_items(
    series: dict,
    model_range: dict,
    line_code: str,
    line: dict,
    transmission_variant: dict,
    market: Market,
) -> LineItem:
    model_code = transmission_variant["configuration"]["modelCode"]

    # For standard lines, there is no specific description about them, but for other lines we have line descriptions.
    if line_code in STANDARD_LINES:
        line_description: str = line_code
    else:
        line_description = line["phrases"][_get_available_language(series, market)][
            "longDescription"
        ]

    model_description = model_range["models"][model_code]["phrases"][
        _get_available_language(series, market)
    ]["longDescription"]
    variant_type = transmission_variant["classifiedConfiguration"]["transmission"][
        "type"
    ]
    # For few models the value of variant type is undefined, in that case we will not concat the variant type with model description.
    if variant_type != "undefined":
        model_description = f"{model_description} - {variant_type}"

    gross_list_price: float = transmission_variant["prices"]["grossPrice"]

    # In case of BMW, GLP and OTR are same.
    on_the_road_price: float = transmission_variant["prices"]["grossListPrice"]

    # Getting the net price after deducting the VAT% for that market.
    net_list_price: float = compute_net_list_price(market, gross_list_price)

    engine_performance_kw = _get_engine_performance(
        transmission_variant, "C_LEIST_GES_KOMM", KW_UNIT
    )
    engine_performance_hp = _get_engine_performance(
        transmission_variant, "C_LEIST_GES_KOMM_PS", HP_UNIT
    )

    if _get_available_language(series, market) in model_range["additionalData"]["description"]:
        model_range_description = model_range["additionalData"]["description"][_get_available_language(series, market)]["longDescription"]
    else:
        model_range_description = str(SWEDEN_G45_DESC)

    return create_line_item(
        date=today_dashed_str(),
        vendor=Vendor.BMW,
        series=series["code"],
        model_range_code=model_range["code"],
        model_range_description=model_range_description,
        model_code=model_code,
        model_description=model_description,
        line_code=line_code,
        line_description=line_description,
        line_option_codes=_generate_line_options(transmission_variant),
        currency=Currency[market].value,
        net_list_price=net_list_price,
        gross_list_price=gross_list_price,
        on_the_road_price=on_the_road_price,
        market=market,
        engine_performance_kw=engine_performance_kw,
        engine_performance_hp=engine_performance_hp,
    )


def _generate_line_options(transmission_variant: dict) -> list[LineItemOptionCode]:
    response = []
    for option in transmission_variant["configuration"]["elements"].keys():
        response.append(create_default_line_item_option_code(option))

    return response


def adjust_line_options(
    market: Market,
    parsed_options: list,
    available_options: dict,
    options_price: dict,
    line_description: str,
) -> list[LineItemOptionCode]:
    response = []
    for option in parsed_options:
        code = option.code
        option_price = options_price.get(code, 0)
        # Filtering based on option_price >= 0 as for few options the prices were in negative.
        if code in available_options and option_price >= 0:
            if line_description != "BASIC_LINE" and available_options[code][
                "optionType"
            ] in ["modelVariant", "line"]:
                continue
            if (
                available_options[code]["optionType"] in ["modelVariant", "line"]
                and option_price != 0
                and option.included
            ):
                option.included = False
            response.append(
                create_line_item_option_code(
                    code=code,
                    type=available_options[code]["optionType"],
                    description=remove_new_line_characters(
                        available_options[code]["phrases"]["longDescription"]
                    ),
                    net_list_price=compute_net_list_price(market, option_price),
                    gross_list_price=option_price,
                    included=option.included,
                )
            )
    return response


def _get_available_language(series: dict, market: Market) -> str:
    if market == Market.NL:
        return "nl"
    return series["availableLanguages"][0]


def parse_api_token(token_content: str) -> str:
    soup = BeautifulSoup(token_content, "html.parser")
    # API Token is stored in the script tag in the form of base64 encoded string stored in JSON,
    # further, it is encoded in the form URI component.
    """
    <script>
      ...
      conApp.inputSettings = JSON.parse(decodeURIComponent(atob("dd")))
    </script>
    """
    script_tag = soup.find("script", string=lambda t: t and "conApp.inputSettings" in t)
    if not script_tag:
        raise ValueError("Script tag containing 'conApp.inputSettings' not found")

    match = re.search(r'atob\((\'|")(.*?)(\'|")\)', script_tag.string)
    if not match:
        raise ValueError("Base64 encoded JSON string not found")

    base64_string = match.group(2)
    try:
        decoded_string = base64.b64decode(base64_string).decode("utf-8")
        json_string = urllib.parse.unquote(decoded_string)
        input_settings_value = json.loads(json_string)
        api_token_key = (
            input_settings_value.get("APP", {})
            .get("backend", {})
            .get("settingsAccessories", {})
            .get("headers", {})
            .get(X_API_KEY, NOT_AVAILABLE)
        )
    except Exception as e:
        raise ValueError(f"Error decoding JSON or Base64: {e}")

    if api_token_key == NOT_AVAILABLE:
        raise ValueError("There are issues in parsing the API token key")

    return api_token_key


def parse_tax_date(
    model_matrix: dict, series: str, model_range_code: str, model_code: str
) -> str:
    return model_matrix[series]["modelRanges"][model_range_code]["models"][model_code][
        "taxDate"
    ]


def parse_effect_date(
    model_matrix: dict, series: str, model_range_code: str, model_code: str
) -> str:
    return model_matrix[series]["modelRanges"][model_range_code]["models"][model_code][
        "effectDate"
    ]


def parse_order_date(
    model_matrix: dict, series: str, model_range_code: str, model_code: str
) -> str:
    return model_matrix[series]["modelRanges"][model_range_code]["models"][model_code][
        "orderDate"
    ]


def parse_options_price(price_details: dict) -> dict:
    prices = {}
    for option in price_details["availableOptions"]:
        prices[option["optionCode"]] = option["grossPrice"]
    return prices


def parse_packages_price(price_details: dict) -> dict:
    prices = {}
    for package_code, package in price_details["packagePricingList"].items():
        prices[package_code] = package["price"]["grossPrice"]
    return prices


def parse_lines_string(model_matrix: dict, line_item: LineItem) -> str:
    all_lines = list(
        model_matrix[line_item.series]["modelRanges"][line_item.model_range_code][
            "lines"
        ].keys()
    )
    possible_lines = []
    option_codes = line_item.line_option_code_keys()
    # This available list of line codes is required for the constructability API. It requires only these line codes which are not already included in the model's options.
    for line in all_lines:
        if line not in option_codes:
            possible_lines.append(line)
    possible_lines.sort()
    return ",".join(possible_lines)


def parse_extra_available_options(
    model_available_options: dict, included_options: set, lines_str: str
) -> str:
    possible_available_options = []
    lines = lines_str.split(",")

    # Filtering out all available options based on some known identities.
    # displayTypeId = options having this property equal to 1, are only visible on the website.
    # optionType = Excluding available options having type "other".
    # option should not be a type of MODVAR, Modell variants/Editions (for AT market)
    for code, details in model_available_options.items():
        if (
            details["displayTypeId"] == 1
            and details["optionType"] != "other"
            and len(details["salesGroupCodes"]) > 0
            and "MODVAR" not in details["salesGroupCodes"]
            and "Modell variants/Editions" not in details["salesGroupCodes"]
            and code not in included_options
            and code not in lines
        ):
            possible_available_options.append(code)
    possible_available_options.sort()
    possible_available_options_str = ",".join(possible_available_options)
    return possible_available_options_str


# Method to return the constructible extra options for trim-line.
def parse_constructible_extra_options_for_line(
    constructability_status: dict,
) -> list[LineItemOptionCode]:
    line_option_codes = []

    # All these constructible options are extra options. So, we are assigning them as included=False.
    for option_code, details in constructability_status.items():
        if details["constructible"]:
            line_option_codes.append(
                create_line_item_option_code(
                    code=option_code,
                    type=MISSING_LINE_OPTION_DETAILS,
                    description=MISSING_LINE_OPTION_DETAILS,
                    net_list_price=0,
                    gross_list_price=0,
                    included=False,
                )
            )

    return line_option_codes


def parse_is_volt_48(is_volt_48_content: dict) -> bool:
    return is_volt_48_content["classifiedConfiguration"]["volt48"]["isVolt48Variant"]


def parse_configuration_state(configuration_state_content: dict) -> str:
    return configuration_state_content["configurationState"]


def _get_engine_performance(transmission_variant, performance_type, unit):
    engine_performance = NOT_AVAILABLE
    # Checking if horsepower is present for specific model or not, if the value is not present it should be 'NA'
    if "otdData" in transmission_variant:
        engine_performance = f"{transmission_variant['otdData'].get('values', {}).get(performance_type, {}).get('targetValue', NOT_AVAILABLE)}"
    # No need to add units for 'NA'
    if engine_performance != NOT_AVAILABLE:
        engine_performance += unit
    return engine_performance


def parse_ix_model_codes(model_matrix) -> list:
    model_codes = []
    for series_code, series in model_matrix.items():
        for model_range_code, model_range in series["modelRanges"].items():
            model_codes.extend(model_range["models"].keys())
    return model_codes
