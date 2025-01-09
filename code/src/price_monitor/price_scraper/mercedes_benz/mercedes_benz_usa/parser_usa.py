import json
import re
from dataclasses import dataclass
from typing import List

from bs4 import BeautifulSoup

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
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


@dataclass(eq=True)
class AvailableModel:
    model_code: str
    line_exists: bool
    build_page: str


@dataclass(eq=True)
class AvailableTrimLine:
    line_code: str
    line_description: str
    line_path: str


class MercedesBenzUSAParser:
    RESULT_NODE = "result"
    ACTIVE_MODELS_NODE = "activeModels"
    LINE_EXISTS = "lineExists"
    MODEL = "model"
    MODEL_BUILD_PAGE = "modelBuildPage"

    def parse_available_models(self, model_data: str) -> [AvailableModel]:
        available_models = []
        active_models = json.loads(model_data)[self.RESULT_NODE][
            self.ACTIVE_MODELS_NODE
        ]

        if not active_models:
            return available_models
        else:
            for model_code in active_models:
                model_build_page = active_models[model_code][self.MODEL_BUILD_PAGE]
                if model_build_page is None:
                    continue
                line_exists = "/lines" in model_build_page
                available_model = AvailableModel(
                    model_code=model_code,
                    line_exists=line_exists,
                    build_page=model_build_page,
                )
                available_models.append(available_model)
        return available_models

    def parse_trim_line(
        self, model_page: str, line_description: str, line_code: str
    ) -> LineItem:
        model_data = self._extract_model_json_from_html(model_page)
        if line_code == "":
            line_code = model_data["baumuster"]
        return create_line_item(
            date=today_dashed_str(),
            vendor=Vendor.MERCEDES_BENZ,
            series=model_data["className"],
            model_range_code=model_data["model"],
            model_range_description=model_data["className"]
            + " "
            + model_data["bodyStyleName"],
            model_code=model_data["baumuster"],
            model_description=model_data["vehicleName"],
            line_code=line_code,
            line_description=line_description,
            currency=Currency[Market.US].value,
            line_option_codes=self.parse_option_codes(model_data["categories"]),
            net_list_price=model_data["msrp"],
            gross_list_price=GROSS_LIST_PRICE_FOR_US,
            market=Market.US,
            engine_performance_kw=NOT_AVAILABLE,
        )

    def parse_option_codes(self, categories: dict) -> List[LineItemOptionCode]:
        line_item_option_code_list: List[LineItemOptionCode] = []
        for super_category, category_data in categories.items():
            category_groups = category_data["groups"]
            for category, sub_category in category_groups.items():
                options = sub_category["options"]
                for option in options:
                    code = option["id"].split(":")[1]
                    line_item_option_code_list.append(
                        create_line_item_option_code(
                            code=code,
                            description=remove_new_line_characters(option["name"]),
                            type=category,
                            net_list_price=option["price"],
                            gross_list_price=GROSS_LIST_PRICE_FOR_US,
                            included=option["defaultSelection"],
                        )
                    )
        return line_item_option_code_list

    def parse_line_codes(self, model_page: str) -> [AvailableTrimLine]:
        model_data = self._extract_line_json_from_html(model_page)
        line_code: str
        line_description: str
        line_path: str
        trim_line_codes: [AvailableTrimLine] = []
        for model in model_data:
            line_code = model["modelLineCode"]
            line_description = model["modelLineName"]
            line_path = model["modelLineBuildPage"].lower()
            trim_line_codes.append(
                AvailableTrimLine(line_code, line_description, line_path)
            )
        return trim_line_codes

    def _extract_line_json_from_html(self, model_page: str) -> List[dict]:
        line_pattern = r"data: \[(.*)(/s*)(.*)]"
        return self._extract_json_from_html(
            model_page=model_page,
            pattern=line_pattern,
            match_group_num=0,
            prefix_arg="data: ",
        )

    def _extract_model_json_from_html(self, model_page: str) -> dict:
        model_pattern = r"MODEL_BYO_CONTENT: [{](.*)(\s*)(.*)[}]"
        return self._extract_json_from_html(
            model_page=model_page,
            pattern=model_pattern,
            match_group_num=1,
            suffix_arg=",",
            separator="{",
        )

    def _extract_json_from_html(
        self,
        model_page: str,
        pattern: str,
        match_group_num: int,
        suffix_arg: str = None,
        prefix_arg: str = None,
        separator: str = None,
    ):
        html_parser = BeautifulSoup(model_page, "html.parser")
        mercedes_usa_model_pattern = re.compile(pattern, re.MULTILINE)

        response_json = {}
        for script in html_parser.find_all("script", {"src": False}):
            if script:
                match = mercedes_usa_model_pattern.search(script.getText())
                if match:
                    if suffix_arg:
                        json_str = separator + match.group(
                            match_group_num
                        ).removesuffix(suffix_arg)
                    elif prefix_arg:
                        json_str = match.group(match_group_num).removeprefix(prefix_arg)
                    response_json = json.loads(json_str)
        return response_json
