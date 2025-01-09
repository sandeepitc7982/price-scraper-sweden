from typing import List

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.constants import NOT_AVAILABLE


def create_line_item(
    date: str,
    vendor: Vendor,
    series: str,
    model_range_code: str,
    model_range_description: str,
    model_code: str,
    model_description: str,
    line_code: str,
    line_description: str,
    line_option_codes: List[LineItemOptionCode],
    currency: str,
    net_list_price: float,
    gross_list_price: float,
    on_the_road_price: float = 0.0,
    market: Market = Market.UK,
    engine_performance_kw: str = NOT_AVAILABLE,
    engine_performance_hp: str = NOT_AVAILABLE,
):
    return LineItem(
        recorded_at=date,
        last_scraped_on=date,
        vendor=vendor,
        series=series,
        model_range_code=model_range_code,
        model_range_description=model_range_description,
        model_code=model_code,
        model_description=model_description,
        line_code=line_code,
        line_description=line_description,
        line_option_codes=line_option_codes,
        currency=currency,
        net_list_price=net_list_price,
        gross_list_price=gross_list_price,
        on_the_road_price=on_the_road_price,
        market=market,
        engine_performance_kw=engine_performance_kw,
        engine_performance_hp=engine_performance_hp,
    )


def create_line_item_option_code(
    code: str,
    type: str,
    description: str,
    net_list_price: float,
    gross_list_price: float,
    included: bool,
) -> LineItemOptionCode:
    return LineItemOptionCode(
        code=code,
        type=type,
        description=description,
        net_list_price=net_list_price,
        gross_list_price=gross_list_price,
        included=included,
    )
