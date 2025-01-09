import unittest
from test.price_monitor.utils.test_data_builder import (
    create_difference_line_item,
    create_test_option_price_difference_item,
)
from unittest.mock import patch

from src.price_monitor.model.create_option_price_difference_item import (
    _create_option_price_difference_item_from_difference,
    create_option_price_difference_item_with_merged_model_range,
)
from src.price_monitor.model.difference_item import DifferenceReason
from src.price_monitor.model.option_price_difference_item import (
    OptionPriceDifferenceItem,
    OptionPriceDifferenceReason,
    build_option_price_difference_item,
)
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.utils.clock import today_dashed_str_with_key


class TestOptionPriceItem(unittest.TestCase):
    def test_build_option_price_item(self):
        expected_result = OptionPriceDifferenceItem(
            recorded_at=today_dashed_str_with_key(),
            vendor=Vendor.BMW,
            market=Market.DE,
            option_description="Car Option",
            option_old_price=100.00,
            option_new_price=80.00,
            perc_change="20%",
            option_price_change=20.00,
            currency="EUR",
            reason=OptionPriceDifferenceReason.PRICE_DECREASE,
            model_range_description="1 coupe, 3 sports back",
        )
        actual_result = build_option_price_difference_item(
            recorded_at=today_dashed_str_with_key(),
            vendor=Vendor.BMW,
            market=Market.DE,
            option_description="Car Option",
            option_old_price=100.00,
            option_new_price=80.00,
            perc_change="20%",
            option_price_change=20.00,
            currency="EUR",
            reason=OptionPriceDifferenceReason.PRICE_DECREASE,
            model_range_description="1 coupe, 3 sports back",
        )
        assert actual_result == expected_result

    def test_create_option_price_difference_item_with_merged_model_range_returns_empty_list_when_there_is_no_option_price_change(
        self,
    ):
        differences = []

        actual_output = create_option_price_difference_item_with_merged_model_range(
            differences
        )

        assert actual_output is None

    def test_create_option_price_difference_item_with_merged_model_range(self):
        differences = [
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                vendor=Vendor.AUDI,
                market=Market.DE,
                model_range_description="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="""
                {
                "option_description": "option_description",
                "old_price": 5000.0
                }
                """,
                new_value="4000.00",
                reason=DifferenceReason.OPTION_PRICE_CHANGE,
            ),
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                vendor=Vendor.AUDI,
                market=Market.DE,
                model_range_description="model_2",
                model_code="model_code_2",
                line_code="audi_cool_model",
                old_value="""
                {
                "option_description": "option_description",
                "old_price": 5000.0
                }
                """,
                new_value="4000.00",
                reason=DifferenceReason.OPTION_PRICE_CHANGE,
            ),
        ]
        expected_output = create_test_option_price_difference_item(
            vendor=Vendor.AUDI,
            market=Market.DE,
            model_range_description="model_1, model_2",
            option_description="option_description",
            option_new_price=4000.00,
            option_old_price=5000.00,
            currency="EUR",
            perc_change="-20%",
            option_price_change=-1000.00,
            reason=OptionPriceDifferenceReason.PRICE_DECREASE,
        )

        actual_output = create_option_price_difference_item_with_merged_model_range(
            differences
        )

        assert actual_output == expected_output

    def test_create_option_price_difference_item_from_difference(self):
        difference_item = create_difference_line_item(
            recorded_at=today_dashed_str_with_key(),
            vendor=Vendor.AUDI,
            market=Market.DE,
            model_range_description="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            old_value="""
                {
                "option_description": "option_description",
                "old_price": 5000.0
                }
                """,
            new_value="4000.00",
            reason=DifferenceReason.OPTION_PRICE_CHANGE,
        )

        expected_output = create_test_option_price_difference_item(
            vendor=Vendor.AUDI,
            market=Market.DE,
            model_range_description="model_1",
            option_description="option_description",
            option_new_price=4000.00,
            option_old_price=5000.00,
            currency="EUR",
            perc_change="-20%",
            option_price_change=-1000.00,
            reason=OptionPriceDifferenceReason.PRICE_DECREASE,
        )

        actual_output = _create_option_price_difference_item_from_difference(
            difference_items=[difference_item], model_range="model_1"
        )

        assert actual_output == expected_output

    @patch("src.price_monitor.model.create_option_price_difference_item.logger")
    def test_create_option_old_value_bad_json_logs_exception_and_returns_empty_option_price_difference(
        self, mocklogger
    ):
        difference_item = create_difference_line_item(
            recorded_at=today_dashed_str_with_key(),
            vendor=Vendor.AUDI,
            market=Market.DE,
            model_range_description="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            old_value="""
                        {
                         "option_description",
                        "old_price": 5000.0
                        }
                        """,
            new_value="4000.00",
            reason=DifferenceReason.OPTION_PRICE_CHANGE,
        )

        actual_output = _create_option_price_difference_item_from_difference(
            difference_items=[difference_item], model_range="model_1"
        )

        mocklogger.exception.assert_called_once()
        assert actual_output is None

    def test_create_option_price_difference_item_with_merged_model_range_when_there_are_multiple_options_with_same_model_range_does_not_duplicate(
        self,
    ):
        differences = [
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                vendor=Vendor.AUDI,
                market=Market.DE,
                model_range_description="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="""
                {
                "option_description": "option_description",
                "old_price": 5000.0
                }
                """,
                new_value="4000.00",
                reason=DifferenceReason.OPTION_PRICE_CHANGE,
            ),
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                vendor=Vendor.AUDI,
                market=Market.DE,
                model_range_description="model_1",
                model_code="model_code_2",
                line_code="audi_cool_model",
                old_value="""
                {
                "option_description": "option_description",
                "old_price": 5000.0
                }
                """,
                new_value="4000.00",
                reason=DifferenceReason.OPTION_PRICE_CHANGE,
            ),
        ]
        expected_output = create_test_option_price_difference_item(
            vendor=Vendor.AUDI,
            market=Market.DE,
            model_range_description="model_1",
            option_description="option_description",
            option_new_price=4000.00,
            option_old_price=5000.00,
            currency="EUR",
            perc_change="-20%",
            option_price_change=-1000.00,
            reason=OptionPriceDifferenceReason.PRICE_DECREASE,
        )

        actual_output = create_option_price_difference_item_with_merged_model_range(
            differences
        )

        assert actual_output == expected_output

    def test_create_option_price_difference_item_with_merged_model_range_when_there_are_multiple_options_with_same_model_range_returns_empty_when_no_price_change(
        self,
    ):
        differences = [
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                vendor=Vendor.AUDI,
                market=Market.DE,
                model_range_description="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="""
                {
                "option_description": "option_description",
                "old_price": 4000.0
                }
                """,
                new_value="4000.00",
                reason=DifferenceReason.OPTION_PRICE_CHANGE,
            ),
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                vendor=Vendor.AUDI,
                market=Market.DE,
                model_range_description="model_1",
                model_code="model_code_2",
                line_code="audi_cool_model",
                old_value="""
                {
                "option_description": "option_description",
                "old_price": 4000.0
                }
                """,
                new_value="4000.00",
                reason=DifferenceReason.OPTION_PRICE_CHANGE,
            ),
        ]

        actual_output = create_option_price_difference_item_with_merged_model_range(
            differences
        )

        assert actual_output is None
