from typing import List

from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import LineItem
from src.price_monitor.utils.clock import (
    today_dashed_str,
    current_timestamp_dashed_str_with_timezone,
    yesterday_timestamp_dashed_str_with_timezone,
)


class LineItemBuilder:
    def __init__(self):
        self._recorded_at = current_timestamp_dashed_str_with_timezone()
        self._last_scraped_on = today_dashed_str()
        self._vendor = Vendor.TESLA
        self._series = "Model Test"
        self._model_range_code = "XFA3"
        self._model_range_description = "R Coupe"
        self._model_code = "MS22"
        self._model_description = "R3"
        self._line_code = "SP"
        self._line_description = "Sport"
        self._line_option_codes = [
            LineItemOptionCode(
                code="TTB",
                description="suspension",
                type="test",
                net_list_price=47,
                gross_list_price=56.53,
                included=False,
            ),
            LineItemOptionCode(
                code="RRS",
                description="brakes",
                type="test",
                net_list_price=47,
                gross_list_price=56.53,
                included=False,
            ),
        ]
        self._currency = "USD"
        self._net_list_price = 81364
        self._gross_list_price = 89500
        self._market = Market.AU

    def build(self) -> LineItem:
        return LineItem(
            recorded_at=self._recorded_at,
            last_scraped_on=self._last_scraped_on,
            vendor=self._vendor,
            series=self._series,
            model_range_code=self._model_range_code,
            model_range_description=self._model_range_description,
            model_code=self._model_code,
            model_description=self._model_description,
            line_code=self._line_code,
            line_description=self._line_description,
            line_option_codes=self._line_option_codes,
            currency=self._currency,
            net_list_price=self._net_list_price,
            gross_list_price=self._gross_list_price,
            market=self._market,
        )

    def with_date(self, recorded_at: str) -> "LineItemBuilder":
        self._recorded_at = recorded_at
        return self

    def with_last_scraped_on(self, last_scraped_on: str) -> "LineItemBuilder":
        self._last_scraped_on = last_scraped_on
        return self

    def with_yesterday_timestamp(self) -> "LineItemBuilder":
        self._recorded_at = yesterday_timestamp_dashed_str_with_timezone()
        return self

    def with_today_timestamp(self) -> "LineItemBuilder":
        self._recorded_at = current_timestamp_dashed_str_with_timezone()
        return self

    def with_vendor(self, vendor: Vendor) -> "LineItemBuilder":
        self._vendor = vendor
        return self

    def with_series(self, series: str) -> "LineItemBuilder":
        self._series = series
        return self

    def with_model_range_code(self, model_range_code: str) -> "LineItemBuilder":
        self._model_range_code = model_range_code
        return self

    def with_model_range_description(
        self, model_range_description: str
    ) -> "LineItemBuilder":
        self._model_range_description = model_range_description
        return self

    def with_model_code(self, model_code: str) -> "LineItemBuilder":
        self._model_code = model_code
        return self

    def with_model_description(self, model_description: str) -> "LineItemBuilder":
        self._model_description = model_description
        return self

    def with_line_code(self, line_code: str) -> "LineItemBuilder":
        self._line_code = line_code
        return self

    def with_line_description(self, line_description: str) -> "LineItemBuilder":
        self._line_description = line_description
        return self

    def with_line_option_code(
        self, line_option_codes: List[LineItemOptionCode]
    ) -> "LineItemBuilder":
        self._line_option_codes = line_option_codes
        return self

    def with_currency(self, currency: str) -> "LineItemBuilder":
        self._currency = currency
        return self

    def with_net_list_price(self, net_list_price: float) -> "LineItemBuilder":
        self._net_list_price = net_list_price
        return self

    def with_gross_list_price(self, gross_list_price: float) -> "LineItemBuilder":
        self._gross_list_price = gross_list_price
        return self

    def with_market(self, market: Market) -> "LineItemBuilder":
        self._market = market
        return self
