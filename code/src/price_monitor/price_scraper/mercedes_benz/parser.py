import re
from typing import List, Set

from loguru import logger

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor
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

LIST_OF_CLASS_NAMES_WITH_KLASSE = [
    "A-KLASSE",
    "B-KLASSE",
    "C-KLASSE",
    "E-KLASSE",
    "G-KLASSE",
    "S-KLASSE",
]


def parse_available_models_links(data: dict) -> Set[str]:
    # Initialize a set to hold unique endpoints for Model Ranges(class/bodytype)
    endpoints = set()

    # Iterate directly over each vehicle class in the data
    for vehicle_class in data:
        # Check if the vehicle class has a class ID
        if "ccsClassId" in vehicle_class:
            ccs_class_id = vehicle_class["ccsClassId"]

            # Iterate over each body type within the vehicle class
            for body_type in vehicle_class["bodytypes"]:
                # Proceed if the body type has an ID
                if "ccsBodytypeId" in body_type:
                    # Iterate over each model within the body type
                    for model in body_type["models"]:
                        # Assume the first vehicle is representative for the model
                        vehicle = model["vehicles"][0]

                        # Filter for passenger cars
                        if vehicle["productGroup"] == "PASSENGER_CAR":
                            # Use ccsId from bodytypeData if available, otherwise use ccsBodytypeId
                            ccs_body_type_id = model.get("bodytypeData", {}).get(
                                "ccsId", body_type["ccsBodytypeId"]
                            )

                            # Construct and add the endpoint to the set
                            endpoint = f"{ccs_class_id}/{ccs_body_type_id}"
                            endpoints.add(endpoint)

    return endpoints


def parse_trim_line_codes(data: dict) -> List[str]:
    trim_line_code: List[str] = []
    component_categories = data["componentCategories"]
    for i in range(len(component_categories)):
        if (
            component_categories[i]["id"] == "VARIANTS"
            or component_categories[i]["id"] == "EXTERIOR"
        ):
            category = component_categories[i]["subcategories"]
            for category_count in range(len(category)):
                is_category_line_or_exterior_style = (
                    category[category_count]["id"] == "LINES"
                    or category[category_count]["id"] == "EXTERIOR_STYLE"
                    or category[category_count]["id"] == ""
                )
                if is_category_line_or_exterior_style:
                    sub_category = category[category_count]["subcategories"]
                    if (
                        sub_category[0]["id"] == "ZK096"
                        or sub_category[0]["id"] == "ZK017"
                    ):
                        _append_option_code(
                            sub_category[0]["componentIds"], trim_line_code
                        )
    return trim_line_code


def parse_line_item(
    vehicle: dict, class_body_names: str, market: Market, engine_performance: str
) -> LineItem:
    series = vehicle["vehicleClass"]
    model_description = vehicle["name"]
    engine_performance_hp, engine_performance_kw = split_engine_performance(
        engine_performance, market, series, class_body_names, model_description
    )
    return create_line_item(
        date=today_dashed_str(),
        vendor=Vendor.MERCEDES_BENZ,
        series=series,
        model_range_code=vehicle["typeClass"],
        model_range_description=class_body_names,
        model_code=vehicle["baumuster"],
        model_description=model_description,
        line_code=vehicle["modelId"],
        line_description=vehicle["name"],
        currency=vehicle["priceInformation"]["configurationPrice"]["currencyISO"],
        line_option_codes=[],
        net_list_price=vehicle["priceInformation"]["configurationPrice"]["netPrice"],
        gross_list_price=vehicle["priceInformation"]["configurationPrice"]["price"],
        on_the_road_price=vehicle["priceInformation"]["configurationPrice"][
            "price"
        ],  # In case of MB, GLP and OTR are same.
        market=market,
        engine_performance_kw=engine_performance_kw,
        engine_performance_hp=engine_performance_hp,
    )


def parse_trim_line(
    market: Market,
    data: dict,
    trim_line_code: str,
    trim_line_description: str,
    engine_performance: str,
) -> LineItem:
    vehicle = data["vehicle"]
    trim_line_description = trim_line_description.replace(
        " Exterieur & AMG Line Interieur", ""
    )
    trim_line_description = trim_line_description.replace("Exterieur", "")
    if trim_line_description == "Mercedes-AMG":
        trim_line_description = "AMG Line"
    series = vehicle["vehicleClass"]
    model_range_description = f"{vehicle['vehicleClass']} {vehicle['vehicleBody']}"
    model_description = vehicle["name"]
    engine_performance_hp, engine_performance_kw = split_engine_performance(
        engine_performance, market, series, model_range_description, model_description
    )

    return create_line_item(
        date=today_dashed_str(),
        vendor=Vendor.MERCEDES_BENZ,
        series=series,
        model_range_code=vehicle["typeClass"],
        model_range_description=model_range_description,
        model_code=vehicle["baumuster"],
        model_description=model_description,
        line_code=vehicle["modelId"] + "/" + trim_line_code,
        line_description=trim_line_description,
        currency=vehicle["priceInformation"]["configurationPrice"]["currencyISO"],
        line_option_codes=[],
        net_list_price=vehicle["priceInformation"]["configurationPrice"]["netPrice"],
        gross_list_price=vehicle["priceInformation"]["configurationPrice"]["price"],
        on_the_road_price=vehicle["priceInformation"]["configurationPrice"][
            "price"
        ],  # In case of MB, GLP and OTR are same.
        market=market,
        engine_performance_kw=engine_performance_kw,
        engine_performance_hp=engine_performance_hp,
    )


def split_engine_performance(
    engine_performance, market, series, model_range_description, model_description
):
    try:
        (
            engine_performance_kw,
            engine_performance_hp,
        ) = parse_engine_performance_kw_and_hp(engine_performance)
    except Exception as e:
        logger.error(
            f"[{market}] Unable to split engine performance [{engine_performance}] for {series}, {model_range_description}, {model_description}. Due to Reason {e}"
        )
        engine_performance_kw, engine_performance_hp = NOT_AVAILABLE, NOT_AVAILABLE
    return engine_performance_hp, engine_performance_kw


def get_option_codes(component_categories: dict, is_line_basic: bool) -> List[str]:
    list_of_component_id = []
    # the component_id's are in nested form for a few component categories.
    # for example : category->subcategory->subcategory->component_id
    for i in range(len(component_categories)):
        if "standardComponentIds" in component_categories[i]:
            component_id = component_categories[i]["standardComponentIds"]
            _append_option_code(component_id, list_of_component_id)
        if "subcategories" not in component_categories[i]:
            continue
        category = component_categories[i]["subcategories"]
        for j in range(len(category)):
            if "componentIds" in category[j]:
                component_id = category[j]["componentIds"]
                _append_option_code(component_id, list_of_component_id)
            if "subcategories" in category[j]:
                subcategories = category[j]["subcategories"]
                for k in range(len(subcategories)):
                    if not is_line_basic and (
                        subcategories[k]["id"] == "ZK096"
                        or subcategories[k]["id"] == "ZK017"
                    ):
                        continue
                    if "componentIds" in subcategories[k]:
                        component_id = subcategories[k]["componentIds"]
                        _append_option_code(component_id, list_of_component_id)
                    if "subcategories" in subcategories[k]:
                        subcategory = subcategories[k]["subcategories"]
                        for count in range(len(subcategory)):
                            if "componentIds" in subcategory[count]:
                                component_id = subcategory[count]["componentIds"]
                                _append_option_code(component_id, list_of_component_id)
    return sorted(list(set(list_of_component_id)))


def _append_option_code(component_id, list_of_component_id):
    for id in component_id:
        if id == "PC-PYF":
            continue
        list_of_component_id.append(id)


def parse_line_options(
    is_type_hierarchy_enabled_mb, data: dict, is_line_basic: bool, line_description: str
) -> List[LineItemOptionCode]:
    line_option_codes: List[LineItemOptionCode] = []
    option_codes = get_option_codes(data["componentCategories"], is_line_basic)
    components = data["components"]
    line_description = line_description.split(" ")[0]
    for code in option_codes:
        if not is_line_basic and (
            "incompatibleWith" in components[code]
            and line_description in components[code]["incompatibleWith"]
        ):
            continue
        if components[code].get("path"):
            path = components[code].get("path")
            split_scraped_type = [None if re.findall(r"\d", x) else x for x in path]
            type = [i for i in split_scraped_type if i is not None]
            if len(type) < 1:
                continue
        else:
            type = [MISSING_LINE_OPTION_DETAILS]
        line_option_codes.append(
            create_line_item_option_code(
                code=components[code]["id"],
                type=_build_option_type(is_type_hierarchy_enabled_mb, type),
                description=remove_new_line_characters(
                    components[code].get("name", MISSING_LINE_OPTION_DETAILS)
                ),
                net_list_price=components[code]["price"]["netPrice"],
                gross_list_price=components[code]["price"]["price"],
                included=components[code]["selected"],
            )
        )
    return line_option_codes


def _build_option_type(is_type_hierarchy_enabled_mb, path: list) -> str:
    if not is_type_hierarchy_enabled_mb:
        if len(path) > 1 and f"{path[-2]}_" in path[-1]:
            return path[-2]
        return path[-1]
    else:
        return ", ".join(path)


# To construct the model_range_description from the end point of the model.
def build_model_range_description(model: str) -> str:
    class_name, body_name = model.split("/")
    # To make extracted class_name compatible with model_range_description.
    if class_name not in LIST_OF_CLASS_NAMES_WITH_KLASSE:
        class_name = class_name.split("-")[0]
    # To make extracted body_name compatible with model_range_description stored, specifically for "LIMOUSINE_LANG".
    if body_name == "LIMOUSINE_LANG":
        body_name = body_name.replace("_", " ")
    return class_name + " " + body_name


def parse_engine_performance_kw_and_hp(engine_performance) -> list[str:str]:
    # Every engine performance are in format 123 kW (524 PS)
    engine_performance_split = engine_performance.split(" (")
    if len(engine_performance_split) < 2:
        return [NOT_AVAILABLE, NOT_AVAILABLE]
    kw, hp = engine_performance_split
    if "\n" in hp:
        hp = hp[:-1]
    hp = hp[:-1]
    return [kw, hp]
