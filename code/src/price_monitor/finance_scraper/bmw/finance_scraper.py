import requests
from loguru import logger

from src.price_monitor.finance_scraper.bmw.constants import BMW_UK_FINANCE_OPTION_URL
from src.price_monitor.finance_scraper.bmw.finance_parser import (
    parse_finance_line_item,
    parse_finance_line_item_for_pcp,
)
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.finance_item_repository import (
    FileSystemFinanceLineItemRepository,
)
from src.price_monitor.price_scraper.bmw.constants import (
    BASE_URL,
    LOCALISATION_PATH,
    MARKET_MAP,
    PUBLIC_PRICING_PATH,
    X_API_KEY,
)
from src.price_monitor.price_scraper.bmw.parser import (
    _get_available_language,
    parse_effect_date,
    parse_is_volt_48,
    parse_order_date,
    parse_tax_date,
)
from src.price_monitor.price_scraper.bmw.scraper import (
    get_configuration_state_and_is_volt_48,
    get_updated_token,
)
from src.price_monitor.price_scraper.constants import E2E_TEST_LIST_SIZE
from src.price_monitor.utils.caller import execute_request
from src.price_monitor.utils.clock import yesterday_dashed_str_with_key


def get_available_options(
    model_matrix, line_item, tax_date, effect_date, market, session, headers, ix_models
):
    language_support = _get_available_language(model_matrix[line_item.series], market)

    url = (
        f"{BASE_URL}{LOCALISATION_PATH}/{MARKET_MAP[market]}/effect-dates/{effect_date}/"
        f"order-dates/{tax_date}/applications/connext/models/"
        f"{line_item.model_code}/options/languages/{language_support}?trim={line_item.line_description}"
    )

    if line_item.model_code in ix_models:
        url = url.replace("bmwCar", "bmwi")

    response = execute_request(method="get", url=url, session=session, headers=headers)

    return response


def get_metallic_paints(
    model_matrix, line_item, tax_date, effect_date, market, session, headers, ix_models
):
    available_options = get_available_options(
        model_matrix,
        line_item,
        tax_date,
        effect_date,
        market,
        session,
        headers,
        ix_models,
    )

    # MET->Metallic paint
    # UNI ->Non-Metallic paint
    metallic_paint_details = []
    non_metallic_paint_details = []
    for key, value in available_options.items():
        if value["familyCode"] == "MET":
            metallic_paint = {
                "option_type": value["optionType"],
                "paint_code": key,
                "paint_description": value["phrases"]["longDescription"],
            }
            metallic_paint_details.append(metallic_paint)
        elif value["familyCode"] == "UNI":
            non_metallic_paint = {
                "option_type": value["optionType"],
                "paint_code": key,
                "paint_description": value["phrases"]["longDescription"],
            }
            non_metallic_paint_details.append(non_metallic_paint)

    return metallic_paint_details, non_metallic_paint_details


def parse_metallic_paint(options_price_details, metallic_paints):
    metallic_paint_prices = []

    for paint_code in metallic_paints:
        for options in options_price_details:
            if options["optionCode"] == paint_code:
                paint_price = {
                    "paint_code": paint_code,
                    "paint_price": options["grossListPrice"],
                }
                metallic_paint_prices.append(paint_price)

    return metallic_paint_prices


def get_options_prices(
    line_item,
    tax_date,
    effect_date,
    market,
    session,
    headers,
    selected_line_option_codes,
    is_volt_48_variant,
    ix_models,
    metallic_paints_code_list,
):
    payload = {
        "settings": {
            "priceTree": "DEFAULT",
            "ignoreInvalidOptionCodes": True,
            "ignoreOptionsWithUndefinedPrices": True,
            "roundingScale": 1,
            "accessoriesMustFitConfiguration": False,
        },
        "validityDates": {"taxDate": tax_date, "effectDate": effect_date},
        "configuration": {
            "model": line_item.model_code,
            "selectedOptions": selected_line_option_codes,
            "availableOptions": metallic_paints_code_list,
        },
        "additionalParams": {
            "isVolt48Variant": {
                "key": "isVolt48Variant",
                "value": is_volt_48_variant,
            }
        },
    }

    url = f"{BASE_URL}{PUBLIC_PRICING_PATH}/{MARKET_MAP[market]}"

    if line_item.model_code in ix_models:
        url = url.replace("bmwCar", "bmwi")

    return execute_request(
        method="post", url=url, headers=headers, session=session, body=payload
    )


def get_lowest_price_metallic_paint(
    metallic_paints,
    line_item,
    tax_date,
    effect_date,
    market,
    session,
    headers,
    selected_line_option_codes,
    is_volt_48_variant,
    ix_models,
):
    metallic_paints_code_list = [paint["paint_code"] for paint in metallic_paints]

    options_prices = get_options_prices(
        line_item,
        tax_date,
        effect_date,
        market,
        session,
        headers,
        selected_line_option_codes,
        is_volt_48_variant,
        ix_models,
        metallic_paints_code_list,
    )

    metallic_paint_prices = parse_metallic_paint(
        options_prices["availableOptions"], metallic_paints_code_list
    )
    metallic_paint_prices.sort(key=lambda paint: paint["paint_price"])

    lowest_price_metallic_paint = {}

    for paint in metallic_paints:
        if paint["paint_code"] == metallic_paint_prices[0]["paint_code"]:
            paint["paint_price"] = metallic_paint_prices[0]["paint_price"]
            lowest_price_metallic_paint = paint

    return lowest_price_metallic_paint


def update_selected_options_with_metallic_paint(
    selected_line_option_codes,
    metallic_paints,
    non_metallic_paints,
    lowest_price_metallic_paint,
):
    # metallic and non-metallic paints list
    paints_to_remove = metallic_paints + non_metallic_paints
    # Remove paint from standard option
    for paint in paints_to_remove:
        if paint["paint_code"] in selected_line_option_codes:
            selected_line_option_codes.remove(paint["paint_code"])

    # Add the lowest price metallic paint to the selected options
    selected_line_option_codes.append(lowest_price_metallic_paint["paint_code"])
    selected_line_option_codes.sort()
    return selected_line_option_codes


class FinanceScraperBMWUk:
    def __init__(
        self,
        finance_line_item_repository: FileSystemFinanceLineItemRepository,
        session,
        config,
    ):
        self.finance_line_item_repository = finance_line_item_repository
        self.config = config
        self.market = Market.UK
        self.session = session
        self.vendor = Vendor.BMW

    def scrape_finance_options_for_uk(self, parsed_line_items, model_matrix):
        response = []
        if self.config.get("e2e_tests"):
            parsed_line_items = parsed_line_items[:E2E_TEST_LIST_SIZE]

        self.token = get_updated_token()

        for line_item in parsed_line_items:
            logger.debug(
                f"Fetching finance options for line item {line_item.series, line_item.model_range_code, line_item.model_range_description, line_item.model_code, line_item.model_description, line_item.line_description}"
            )
            finance_line_items = self.get_finance_option_for_line(
                line_item, model_matrix
            )
            response.extend(finance_line_items)

        logger.info(f"[UK] scraped {len(response)} Finance Items for BMW")
        return response

    def get_finance_option_for_line(self, line_item, model_matrix):
        response = []
        headers = {
            "Content-Type": "application/json",
            X_API_KEY: self.token,
        }
        try:
            selected_line_option_codes = list(line_item.line_option_code_keys())
            selected_line_option_codes.sort()

            tax_date = parse_tax_date(
                model_matrix=model_matrix,
                series=line_item.series,
                model_range_code=line_item.model_range_code,
                model_code=line_item.model_code,
            )

            effect_date = parse_effect_date(
                model_matrix,
                line_item.series,
                line_item.model_range_code,
                line_item.model_code,
            )

            state_and_is_volt_48_content = get_configuration_state_and_is_volt_48(
                model_code=line_item.model_code,
                effect_date=effect_date,
                included_options_str=",".join(selected_line_option_codes),
                ix_models=self.IX_MODELS,
                headers=headers,
                session=requests.Session(),
                market=Market.UK,
            )

            is_volt_48_variant = parse_is_volt_48(state_and_is_volt_48_content)

            # Get metallic paint list and non-metallic paint list
            metallic_paints, non_metallic_paints = get_metallic_paints(
                model_matrix,
                line_item,
                tax_date,
                effect_date,
                self.market,
                self.session,
                headers,
                self.IX_MODELS,
            )

            # Get the lowest price metallic paint details
            lowest_price_metallic_paint = get_lowest_price_metallic_paint(
                metallic_paints,
                line_item,
                tax_date,
                effect_date,
                self.market,
                self.session,
                headers,
                selected_line_option_codes,
                is_volt_48_variant,
                self.IX_MODELS,
            )

            # Update selected line option codes with the lowest price metallic paint
            updated_line_option_codes = update_selected_options_with_metallic_paint(
                selected_line_option_codes,
                metallic_paints,
                non_metallic_paints,
                lowest_price_metallic_paint,
            )

            payload = {
                "settings": {
                    "application": "CONX",
                    "taxDate": parse_tax_date(
                        model_matrix,
                        line_item.series,
                        line_item.model_range_code,
                        line_item.model_code,
                    ),
                    "effectDate": effect_date,
                    "orderDate": parse_order_date(
                        model_matrix,
                        line_item.series,
                        line_item.model_range_code,
                        line_item.model_code,
                    ),
                },
                "vehicle": {
                    "modelCode": line_item.model_code,
                    "isVolt48Variant": is_volt_48_variant,
                    "selectedEquipments": updated_line_option_codes,
                },
            }
            headers = {
                "content-type": "application/json",
            }
            url = BMW_UK_FINANCE_OPTION_URL
            if line_item.model_code in self.IX_MODELS:
                url = url.replace("bmwCar", "bmwi")
            request_response = execute_request(
                "post", url, headers=headers, body=payload
            )
            for finance_option in request_response["financeProductList"]:
                finance_line_item = self.get_finance_line_item_for_finance_option(
                    line_item,
                    payload,
                    finance_option["productId"],
                    lowest_price_metallic_paint,
                )
                if finance_line_item is None:
                    logger.error(
                        f"Unable to fetch finance option details for {finance_option['productId']} for line item {line_item.series, line_item.model_range_code, line_item.model_range_description, line_item.model_code, line_item.model_description, line_item.line_description}"
                    )
                else:
                    response.append(finance_line_item)
            logger.info(
                f"Got {len(response)} finance options for line item {line_item.series, line_item.model_range_code, line_item.model_range_description, line_item.model_code, line_item.model_description, line_item.line_description}"
            )
        except requests.exceptions.HTTPError as e:
            response = self.finance_line_item_repository.load_model_filter_by_line_code(
                yesterday_dashed_str_with_key(),
                Market.UK,
                Vendor.BMW,
                line_item.series,
                line_item.model_range_code,
                line_item.model_code,
                line_item.line_code,
            )
            if e.response.status_code not in [500, 504]:
                logger.error(
                    f"Unable to fetch finance option details for line item {line_item.series, line_item.model_range_code, line_item.model_range_description, line_item.model_code, line_item.model_description, line_item.line_description}, Reason: {e}"
                )
            else:
                logger.error(
                    f"There API failing to fetch finance option details for line item {line_item.series, line_item.model_range_code, line_item.model_range_description, line_item.model_code, line_item.model_description, line_item.line_description}, Reason: {e}"
                )
        except Exception as e:
            response = self.finance_line_item_repository.load_model_filter_by_line_code(
                yesterday_dashed_str_with_key(),
                Market.UK,
                Vendor.BMW,
                line_item.series,
                line_item.model_range_code,
                line_item.model_code,
                line_item.line_code,
            )
            logger.error(
                f"Unable to fetch finance option details for line item {line_item.series, line_item.model_range_code, line_item.model_range_description, line_item.model_code, line_item.model_description, line_item.line_description}, Reason: {e}"
            )
        return response

    def get_finance_line_item_for_finance_option(
        self, line_item, payload, product_id, lowest_price_metallic_paint
    ):
        payload["financeProduct"] = {
            "productId": product_id,
            "parameters": [
                {"id": "annualMileage", "value": 10000},
                {"id": "downPaymentAmount/grossAmount", "value": 4999},
                {"id": "term", "value": 48},
            ],
        }
        headers = {
            "content-type": "application/json",
        }
        url = BMW_UK_FINANCE_OPTION_URL
        if line_item.model_code in self.IX_MODELS:
            url = url.replace("bmwCar", "bmwi")
        response = execute_request("post", url, headers=headers, body=payload)
        if "PCP" in product_id:
            line_item = parse_finance_line_item_for_pcp(
                line_item,
                product_id,
                response["financeProductList"][0]["parameters"],
                lowest_price_metallic_paint,
            )
            return line_item
        else:
            for ele in response["financeProductList"][0]["parameters"]:
                if ele["id"] == "installment/grossAmount":
                    line_item = parse_finance_line_item(
                        line_item, product_id, ele["value"]
                    )
                    return line_item

        return None
