import dataclasses
import typing
from dataclasses import dataclass

from dataclasses_avroschema import AvroModel

from src.price_monitor.model.difference_item import (
    DifferenceItem,
    DifferenceReason,
    build_difference_for,
)
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_scraper.constants import NOT_AVAILABLE
from src.price_monitor.utils.clock import (
    today_dashed_str,
    current_timestamp_dashed_str_with_timezone,
)
from src.price_monitor.utils.utils import validate_not_blank_or_empty


@dataclass(eq=True)
class LineItem(AvroModel):
    recorded_at: str | None = dataclasses.field(default=None, compare=False)
    vendor: Vendor | None = dataclasses.field(default=None)
    series: str | None = dataclasses.field(default=None)
    model_range_code: str | None = dataclasses.field(default=None)
    model_range_description: str | None = dataclasses.field(default=None, compare=False)
    model_code: str | None = dataclasses.field(default=None)
    model_description: str | None = dataclasses.field(default=None, compare=False)
    line_code: str | None = dataclasses.field(default=None)
    line_description: str | None = dataclasses.field(default=None, compare=False)
    line_option_codes: typing.List[LineItemOptionCode] | None = dataclasses.field(
        compare=False, default=None
    )
    currency: str | None = dataclasses.field(default=None, compare=False)
    net_list_price: float | None = dataclasses.field(default=None, compare=False)
    gross_list_price: float | None = dataclasses.field(default=None, compare=False)
    on_the_road_price: float = dataclasses.field(compare=False, default=0.0)
    market: Market = dataclasses.field(default=Market.UK)
    engine_performance_kw: str = dataclasses.field(compare=False, default=NOT_AVAILABLE)
    engine_performance_hp: str = dataclasses.field(compare=False, default=NOT_AVAILABLE)
    last_scraped_on: str | None = dataclasses.field(compare=False, default=None)
    is_current: bool | None = dataclasses.field(compare=False, default=None)

    def __post_init__(self):
        self.recorded_at = current_timestamp_dashed_str_with_timezone()
        self.is_current = self._calculate_is_current()

        # validate required fields
        validate_not_blank_or_empty(self.recorded_at, "recorded_at")
        validate_not_blank_or_empty(self.market, "market")
        validate_not_blank_or_empty(self.vendor, "vendor")
        validate_not_blank_or_empty(self.series, "series")
        validate_not_blank_or_empty(self.model_range_code, "model_range_code")
        validate_not_blank_or_empty(
            self.model_range_description, "model_range_description"
        )
        validate_not_blank_or_empty(self.model_code, "model_code")
        validate_not_blank_or_empty(self.model_description, "model_description")
        validate_not_blank_or_empty(self.line_code, "line_code")
        validate_not_blank_or_empty(self.line_description, "line_description")

    def _calculate_is_current(self) -> bool | None:
        if self.last_scraped_on:
            # Since date represents when the item was last written to disk, instead of the true current date
            # We need to rely on another source of time, so we will currently use today's date to evaluate freshness
            return self.last_scraped_on == today_dashed_str()

        return None

    def line_option_code_keys(self) -> set:
        response = [option.code for option in self.line_option_codes]
        return set(response)

    def get_line_options_description(self) -> dict:
        response = {}
        for option in self.line_option_codes:
            response[option.code] = option.description
        return response

    def get_line_option_code_details(self) -> dict:
        response = {}
        for option in self.line_option_codes:
            response[option.code] = {
                "description": option.description,
                "included": option.included,
                "gross_list_price": option.gross_list_price,
                "net_list_price": option.net_list_price,
            }
        return response

    def difference_with(self, other: "LineItem") -> list[DifferenceItem]:
        differences: list[DifferenceItem] = []
        # Only compare line items for same car model
        if other != self:
            return differences

        # Check if self's price is different from other's
        if float(self.net_list_price) != float(other.net_list_price):
            differences.append(
                build_difference_for(
                    line_item=self,
                    new_value=str(self.net_list_price),
                    old_value=str(other.net_list_price),
                    reason=DifferenceReason.PRICE_CHANGE,
                )
            )

        differences.extend(self.check_differences_for_options_inclusion(other))
        differences.extend(self.check_differences_for_option_price_change(other))

        # Check if list of option codes has changed
        if self.line_option_code_keys() != other.line_option_code_keys():
            current_descriptions = self.get_line_options_description()
            yesterday_descriptions = other.get_line_options_description()

            # Check for new option codes in self
            for option_code, option_description in current_descriptions.items():
                if (
                    option_code not in yesterday_descriptions
                    and option_description not in yesterday_descriptions.values()
                ):
                    differences.append(
                        build_difference_for(
                            line_item=self,
                            new_value=f"{option_code}-{option_description}",
                            reason=DifferenceReason.OPTION_ADDED,
                        )
                    )
            for option_code, option_description in yesterday_descriptions.items():
                if (
                    option_code not in current_descriptions
                    and option_description not in current_descriptions.values()
                ):
                    differences.append(
                        build_difference_for(
                            line_item=self,
                            old_value=f"{option_code}-{option_description}",
                            reason=DifferenceReason.OPTION_REMOVED,
                        )
                    )

        return differences

    def check_differences_for_options_inclusion(self, other) -> list[DifferenceItem]:
        today_line_options_inclusion = self.get_line_option_code_details()
        yesterday_line_options_inclusion = other.get_line_option_code_details()
        differences = []
        if today_line_options_inclusion != yesterday_line_options_inclusion:
            for code, option_details in yesterday_line_options_inclusion.items():
                if (
                    code in today_line_options_inclusion
                    and option_details["included"]
                    != today_line_options_inclusion[code]["included"]
                ):
                    if not option_details["included"]:
                        reason = DifferenceReason.OPTION_INCLUDED
                        old_value = (
                            str(other.net_list_price)
                            + "/"
                            + str(option_details["gross_list_price"])
                            + "/"
                            + str(option_details["net_list_price"])
                        )
                    else:
                        reason = DifferenceReason.OPTION_EXCLUDED
                        old_value = str(other.net_list_price)
                    differences.append(
                        build_difference_for(
                            line_item=self,
                            old_value=old_value,
                            new_value=str(self.net_list_price) + "/" + code,
                            reason=reason,
                        )
                    )
        return differences

    def check_differences_for_option_price_change(self, other) -> list[DifferenceItem]:
        today_line_options_inclusion = self.get_line_option_code_details()
        yesterday_line_options_inclusion = other.get_line_option_code_details()
        differences: list[DifferenceItem] = []
        if today_line_options_inclusion != yesterday_line_options_inclusion:
            for code, option_details in yesterday_line_options_inclusion.items():
                if (
                    code in today_line_options_inclusion
                    and option_details["net_list_price"]
                    != today_line_options_inclusion[code]["net_list_price"]
                ):
                    reason = DifferenceReason.OPTION_PRICE_CHANGE

                    option_description = option_details["description"].replace(
                        '"', " inch"
                    )
                    option_old_price = option_details["net_list_price"]
                    old_value = f'{{"option_description":"{option_description}","old_price":"{option_old_price}"}}'

                    differences.append(
                        build_difference_for(
                            line_item=self,
                            old_value=old_value,
                            new_value=str(
                                today_line_options_inclusion[code]["net_list_price"]
                            ),
                            reason=reason,
                        )
                    )

        return differences
