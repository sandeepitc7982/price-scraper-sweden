from src.price_monitor.model.vendor import Currency, Market, Vendor
from src.price_monitor.price_scraper.constants import (
    GROSS_LIST_PRICE_FOR_US,
    NOT_AVAILABLE,
)
from src.price_monitor.utils.clock import today_dashed_str
from src.price_monitor.utils.line_item_factory import (
    create_line_item,
    create_line_item_option_code,
)
from src.price_monitor.utils.utils import remove_new_line_characters


def parse_model_code_list_from_json(model_list_json: dict) -> set:
    model_code_list = set()

    for series in model_list_json.values():
        model_ranges = series["bodyStyles"]

        for model_range in model_ranges:
            models = model_range["models"]
            for model in models:
                model_code_list.add(model["code"])
    return model_code_list


def parse_line_items(model_details):
    line_items = []

    is_design_list_empty = len(model_details["configuration"]["designs"]) == 0

    if is_design_list_empty:
        line_item = extract_line_item(
            model_details, line_code="BASIC_LINE", line_description="BASIC_LINE"
        )
        return [line_item]

    # Designs list will contain all the available line items for that model
    for design in model_details["configuration"]["designs"]:
        line_description = model_details["optionDetails"][design["code"]]["name"]
        line_item = extract_line_item(model_details, design["code"], line_description)
        line_items.append(line_item)

    return line_items


def extract_line_item(model_details, line_code, line_description):
    line_item = create_line_item(
        date=today_dashed_str(),
        vendor=Vendor.BMW,
        series=model_details["model"]["series"],
        model_range_code=model_details["model"]["modelRange"],
        model_range_description=model_details["model"]["bodyStyle"],
        model_code=model_details["model"]["code"],
        model_description=model_details["model"]["name"],
        line_code=line_code,
        line_description=line_description,
        line_option_codes=[],
        currency=Currency[Market.US].value,
        net_list_price=model_details["model"]["price"],
        gross_list_price=GROSS_LIST_PRICE_FOR_US,
        market=Market.US,
        engine_performance_kw=NOT_AVAILABLE,
    )
    return line_item


def parse_all_available_options(line_details, option_details):
    # List of options type we are parsing.
    option_types = [
        "accessories",
        "colors",
        "options",
        "packages",
        "trims",
        "upholstery",
        "wheels",
        "vehiclePrograms",
    ]
    line_item_options = []
    for option_type in option_types:
        option_type_details = line_details["configuration"][option_type]

        # Sometimes we have options in nested form. So first we fetch the upper dict for each sub option type,
        # and then inside list of options.
        if isinstance(option_type_details, dict):
            for key, options_list in option_type_details.items():
                line_item_options.extend(
                    generate_line_item_options(
                        option_details, option_type, options_list
                    )
                )
        else:
            line_item_options.extend(
                generate_line_item_options(
                    option_details, option_type, option_type_details
                )
            )
    return line_item_options


def generate_line_item_options(option_details, option_type, options_list):
    line_item_options = []

    for option in options_list:
        option_code = option["code"]
        description = remove_new_line_characters(option_details[option_code]["name"])
        if "deletion" in description:
            continue
        line_item_options.append(
            create_line_item_option_code(
                code=option_code,
                description=description,
                type=option_type,
                included=option["isSelected"],
                net_list_price=option["price"],
                gross_list_price=option["price"],
            )
        )

    return line_item_options


# Currently, gross and net prices are the same for now. As we don't have proper tax info for US.
def extract_price(line_details):
    return line_details["configuration"]["price"]


def parse_extra_designs_list(line_details):
    design_codes = []
    designs = line_details["configuration"]["designs"]
    for design in designs:
        if design["isSelected"] is False:
            design_codes.append(design["code"])
    return design_codes


def parse_is_option_constructible(
    extra_designs_list: list, options_constructability_json: dict
) -> bool:
    for extra_design in extra_designs_list:
        # So, after adding that option to our line, if that option require different line,
        # then different line code will also be added in the changeInfo, so on that basis we can check whether
        # it is constructible or not.
        if (
            "changeInfo" in options_constructability_json["configuration"]
            and extra_design
            in options_constructability_json["configuration"]["changeInfo"][
                "addItems"
            ].keys()
        ):
            return False
    return True
