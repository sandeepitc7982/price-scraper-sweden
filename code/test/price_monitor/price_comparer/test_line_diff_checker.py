import unittest
from test.price_monitor.builder.line_item_builder import LineItemBuilder
from test.price_monitor.utils.test_data_builder import (
    create_difference_line_item,
    create_test_difference_item,
    create_test_line_item,
    create_test_line_item_option_code,
    create_test_option_price_difference_item,
)

from src.price_monitor.model.create_option_price_difference_item import (
    create_option_price_difference_item,
)
from src.price_monitor.model.create_price_difference_item import (
    create_price_difference_item,
    create_price_difference_item_with_merged_reason,
)
from src.price_monitor.model.difference_item import (
    DifferenceItem,
    DifferenceReason,
    build_difference_for,
)
from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.option_price_difference_item import (
    OptionPriceDifferenceItem,
    OptionPriceDifferenceReason,
)
from src.price_monitor.model.price_difference_item import PriceDifferenceReason
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_comparer.line_diff_checker import check_item_differences
from src.price_monitor.utils.clock import (
    today_dashed_str,
    today_dashed_str_with_key,
    yesterday_dashed_str_with_key,
)


class TestLineDiffChecker(unittest.TestCase):
    def test_detects_new_line(self):
        new_line = LineItemBuilder().with_today_timestamp().with_series("C").build()

        prev_dataset = [
            LineItemBuilder().with_yesterday_timestamp().with_series("A").build(),
            LineItemBuilder().with_yesterday_timestamp().with_series("B").build(),
        ]
        current_dataset = [
            LineItemBuilder().with_today_timestamp().with_series("A").build(),
            LineItemBuilder().with_today_timestamp().with_series("B").build(),
            new_line,
        ]

        actual = check_item_differences(current=current_dataset, previous=prev_dataset)[
            0
        ]

        assert actual == [
            build_difference_for(line_item=new_line, reason=DifferenceReason.NEW_LINE)
        ]

    def test_detects_removed_line(self):
        removed_line = (
            LineItemBuilder().with_yesterday_timestamp().with_series("C").build()
        )

        prev_dataset = [LineItemBuilder().build(), removed_line]

        current_dataset = [LineItemBuilder().build()]

        assert check_item_differences(current=current_dataset, previous=prev_dataset)[
            0
        ] == [
            build_difference_for(
                line_item=removed_line, reason=DifferenceReason.LINE_REMOVED
            )
        ]

    def test_detects_price_change_same_model(self):
        yesterday_model_a = create_test_line_item(
            series="A", net_list_price=500, gross_list_price=550
        )
        yesterday_model_b = create_test_line_item(
            series="B", net_list_price=750, gross_list_price=825
        )
        yesterday_dataset = [yesterday_model_a, yesterday_model_b]

        today_model_a = create_test_line_item(
            series="A", net_list_price=550, gross_list_price=605, currency="eur"
        )
        today_model_b = create_test_line_item(
            series="B", net_list_price=800, gross_list_price=880, currency="eur"
        )
        today_dataset = [today_model_a, today_model_b]

        differences = check_item_differences(today_dataset, yesterday_dataset)

        expected_differences = [
            create_difference_line_item(
                series="A",
                old_value="500",
                new_value="550",
                reason=DifferenceReason.PRICE_CHANGE,
            ),
            create_difference_line_item(
                series="B",
                old_value="750",
                new_value="800",
                reason=DifferenceReason.PRICE_CHANGE,
            ),
        ]

        assert differences[0][0] == expected_differences[0]
        assert differences[0][1] == expected_differences[1]

    def test_does_not_detect_price_change_same_model_different_market(self):
        market_1_model = LineItemBuilder().with_market(Market.AT)
        market_2_model = LineItemBuilder().with_market(Market.AU)

        prev_dataset = [
            market_1_model.with_gross_list_price(500).build(),
            market_2_model.with_gross_list_price(1000).build(),
        ]

        current_dataset = [
            market_1_model.with_gross_list_price(500).build(),
            market_2_model.with_gross_list_price(990).build(),
        ]

        assert (
            build_difference_for(
                line_item=market_1_model.build(),
                reason=DifferenceReason.PRICE_CHANGE,
                old_value="500",
                new_value="990",
            )
            not in check_item_differences(
                current=current_dataset, previous=prev_dataset
            )[0]
        )

    def test_detects_option_added_when_code_and_description_both_changes_or_present_in_current(
        self,
    ):
        prev_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    )
                ]
            )
            .build(),
        ]

        current_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                    LineItemOptionCode(
                        code="STR",
                        type="steering",
                        description="Steering",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        assert check_item_differences(current=current_dataset, previous=prev_dataset)[
            0
        ] == [
            build_difference_for(
                line_item=LineItemBuilder().build(),
                reason=DifferenceReason.OPTION_ADDED,
                new_value="STR-Steering",
            )
        ]

    def test_option_becomes_included_when_todays_data_has_a_new_option_included_in_model(
        self,
    ):
        prev_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=False,
                    )
                ]
            )
            .build(),
        ]

        current_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        assert check_item_differences(current=current_dataset, previous=prev_dataset)[
            0
        ] == [
            build_difference_for(
                line_item=LineItemBuilder().build(),
                reason=DifferenceReason.OPTION_INCLUDED,
                old_value="81364/0/0",
                new_value="81364/BRK",
            )
        ]

    def test_option_becomes_excluded_when_todays_data_has_a_new_option_excluded_in_model(
        self,
    ):
        prev_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    )
                ]
            )
            .build(),
        ]

        current_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=False,
                    ),
                ]
            )
            .build()
        ]

        assert check_item_differences(current=current_dataset, previous=prev_dataset)[
            0
        ] == [
            build_difference_for(
                line_item=LineItemBuilder().build(),
                reason=DifferenceReason.OPTION_EXCLUDED,
                old_value="81364",
                new_value="81364/BRK",
            )
        ]

    def test_detects_option_removed_when_code_and_description_both_changes_or_not_present(
        self,
    ):
        prev_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                    LineItemOptionCode(
                        code="STR",
                        type="steering",
                        description="Steering",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        current_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        assert check_item_differences(current=current_dataset, previous=prev_dataset)[
            0
        ] == [
            build_difference_for(
                line_item=LineItemBuilder().build(),
                reason=DifferenceReason.OPTION_REMOVED,
                old_value="STR-Steering",
            )
        ]

    def test_does_not_detect_change_for_descriptions(self):
        prev_dataset = [
            LineItemBuilder()
            .with_vendor(Vendor.AUDI)
            .with_series("V1")
            .with_model_range_description("description V1")
            .with_model_description("model V1")
            .with_line_description("line V1")
            .build(),
            LineItemBuilder()
            .with_vendor(Vendor.BMW)
            .with_series("V2")
            .with_model_range_description("description V2")
            .with_model_description("model V2")
            .with_line_description("line V2")
            .build(),
        ]

        current_dataset = [
            LineItemBuilder()
            .with_vendor(Vendor.AUDI)
            .with_series("V1")
            .with_model_range_description("new description V1")
            .with_model_description("new model V1")
            .with_line_description("new line V1")
            .build(),
            LineItemBuilder()
            .with_vendor(Vendor.BMW)
            .with_series("V2")
            .with_model_range_description("new description V2")
            .with_model_description("new model V2")
            .with_line_description("new line V2")
            .build(),
        ]

        assert (
            check_item_differences(current=current_dataset, previous=prev_dataset)[0]
            == []
        )

    def test_check_price_difference_returns_an_empty_list_if_no_differences_between_line_items(
        self,
    ):
        price_differences = create_price_difference_item([])

        assert price_differences == []

    def test_check_price_difference_returns_elements_with_price_increase_if_net_list_price_is_higher_today_than_yesterday(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            line_code="audi_cool_model",
            net_list_price=10000.0,
            gross_list_price=12000.0,
        )
        line_item2_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            line_code="audi_a3",
            net_list_price=12000.0,
            gross_list_price=14000.0,
        )

        line_item1_yesterday = create_test_line_item(
            recorded_at=yesterday_dashed_str_with_key(),
            line_code="audi_cool_model",
            net_list_price=9000.0,
            gross_list_price=10000.0,
        )
        line_item2_yesterday = create_test_line_item(
            recorded_at=yesterday_dashed_str_with_key(),
            line_code="audi_a3",
            net_list_price=9000.0,
            gross_list_price=10000.0,
            line_option_codes=[create_test_line_item_option_code("audi_option_added")],
        )

        expected_price_differences = [
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=line_item1_yesterday.net_list_price,
                new_price=line_item1_today.net_list_price,
                perc_change="11%",
                model_price_change=1000.0,
                reason=PriceDifferenceReason.PRICE_INCREASE,
            ),
            create_test_difference_item(
                line_item=line_item2_today,
                old_price=line_item2_yesterday.net_list_price,
                new_price=line_item2_today.net_list_price,
                perc_change="33%",
                model_price_change=3000.0,
                reason=PriceDifferenceReason.PRICE_INCREASE,
            ),
        ]

        actual = create_price_difference_item(
            check_item_differences(
                current=[line_item1_today, line_item2_today],
                previous=[line_item1_yesterday, line_item2_yesterday],
            )[0]
        )

        assert actual == expected_price_differences

    def test_check_price_difference_returns_elements_with_price_decrease_if_net_list_price_is_lower_today_than_yesterday(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            line_code="audi_cool_model",
            net_list_price=10000.0,
            gross_list_price=12000.0,
        )
        line_item2_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            line_code="audi_a3",
            net_list_price=12000.0,
            gross_list_price=14000.0,
        )

        line_item1_yesterday = create_test_line_item(
            recorded_at=yesterday_dashed_str_with_key(),
            line_code="audi_cool_model",
            net_list_price=14000.0,
            gross_list_price=13000.0,
        )
        line_item2_yesterday = create_test_line_item(
            recorded_at=yesterday_dashed_str_with_key(),
            line_code="audi_a3",
            net_list_price=15000.0,
            gross_list_price=14500.0,
            line_option_codes=[create_test_line_item_option_code("audi_option_added")],
        )

        expected_price_differences = [
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=line_item1_yesterday.net_list_price,
                new_price=line_item1_today.net_list_price,
                perc_change="29%",
                model_price_change=-4000.0,
                reason=PriceDifferenceReason.PRICE_DECREASE,
            ),
            create_test_difference_item(
                line_item=line_item2_today,
                old_price=line_item2_yesterday.net_list_price,
                new_price=line_item2_today.net_list_price,
                perc_change="20%",
                model_price_change=-3000.0,
                reason=PriceDifferenceReason.PRICE_DECREASE,
            ),
        ]

        actual = create_price_difference_item(
            check_item_differences(
                current=[line_item1_today, line_item2_today],
                previous=[line_item1_yesterday, line_item2_yesterday],
            )[0]
        )

        assert actual == expected_price_differences

    def test_check_price_difference_return_price_difference_item_when_option_becomes_included(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="abc", net_list_price=10, included=True
                )
            ],
        )
        line_item1_yesterday = create_test_line_item(
            recorded_at=yesterday_dashed_str_with_key(),
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="abc", gross_list_price=10, net_list_price=10, included=False
                ),
            ],
        )
        expected_price_difference = create_test_difference_item(
            line_item=line_item1_today,
            old_price=0,
            new_price=0,
            perc_change="0%",
            model_price_change=0,
            reason=PriceDifferenceReason.OPTION_INCLUDED,
            option_code="abc",
            option_gross_list_price=10.0,
            option_net_list_price=10.0,
        )

        actual = create_price_difference_item(
            check_item_differences(
                current=[line_item1_today],
                previous=[line_item1_yesterday],
            )[0]
        )
        assert actual[0] == expected_price_difference

    def test_check_price_difference_return_price_difference_item_when_option_becomes_excluded(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="abc", net_list_price=10, included=False
                )
            ],
        )
        line_item1_yesterday = create_test_line_item(
            recorded_at=yesterday_dashed_str_with_key(),
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="abc", net_list_price=10, included=True
                ),
            ],
        )
        expected_price_difference = create_test_difference_item(
            line_item=line_item1_today,
            old_price=0,
            new_price=0,
            perc_change="0%",
            model_price_change=0,
            reason=PriceDifferenceReason.OPTION_EXCLUDED,
            option_code="abc",
        )

        actual = create_price_difference_item(
            check_item_differences(
                current=[line_item1_today],
                previous=[line_item1_yesterday],
            )[0]
        )
        assert actual[0] == expected_price_difference

    def testcreate_price_difference_item_returns_difference_item_reason_price_increase_and_option_included_when_there_are_two_reasons(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            model_range_code="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="abc", gross_list_price=0, net_list_price=0, included=True
                )
            ],
            gross_list_price=5000.00,
            net_list_price=5000.00,
        )
        line_item2_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            model_range_code="model_2",
            model_code="model_code_2",
            line_code="audi_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="xyz", gross_list_price=0, net_list_price=0, included=False
                )
            ],
            gross_list_price=3000.00,
            net_list_price=3000.00,
        )
        line_item1_yesterday = create_test_line_item(
            recorded_at=yesterday_dashed_str_with_key(),
            model_range_code="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="abc",
                    gross_list_price=10.00,
                    net_list_price=10.00,
                    included=False,
                ),
            ],
            gross_list_price=4000.00,
            net_list_price=4000.00,
        )
        line_item2_yesterday = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            model_range_code="model_2",
            model_code="model_code_2",
            line_code="audi_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="xyz", gross_list_price=0, net_list_price=0, included=True
                )
            ],
            gross_list_price=3500.00,
            net_list_price=3500.00,
        )
        expected_price_difference = [
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=4000.0,
                new_price=5000.00,
                perc_change="25%",
                model_price_change=1000.00,
                reason=PriceDifferenceReason.PRICE_INCREASE_OPTION_INCLUDED,
                option_code="abc",
                option_gross_list_price=10.00,
                option_net_list_price=10.00,
            ),
            create_test_difference_item(
                line_item=line_item2_today,
                old_price=3500.00,
                new_price=3000.00,
                perc_change="14%",
                model_price_change=-500.00,
                reason=PriceDifferenceReason.PRICE_DECREASE_OPTION_EXCLUDED,
                option_code="xyz",
                option_net_list_price=0,
                option_gross_list_price=0,
            ),
        ]

        actual = create_price_difference_item(
            check_item_differences(
                current=[line_item1_today, line_item2_today],
                previous=[line_item1_yesterday, line_item2_yesterday],
            )[0]
        )

        assert actual == expected_price_difference

    def test_create_price_difference_item_with_merged_reason_returns_price_difference_item_with_one_reason(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            model_range_code="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            gross_list_price=5000.00,
            net_list_price=5000.00,
        )
        difference_item = create_difference_line_item(
            recorded_at=today_dashed_str_with_key(),
            model_range_code="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            old_value="4000.00",
            new_value="5000.00",
            reason=DifferenceReason.PRICE_CHANGE,
        )
        expected_price_difference = [
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=4000.0,
                new_price=5000.00,
                perc_change="25%",
                model_price_change=1000.00,
                reason=PriceDifferenceReason.PRICE_INCREASE,
            )
        ]

        actual = create_price_difference_item_with_merged_reason([difference_item])

        assert actual == expected_price_difference

    def test_create_price_difference_item_with_merged_reason_returns_price_difference_item_with_price_increase_and_option_included_as_reasons_it_merges_the_reason(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            model_range_code="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="xyz", gross_list_price=10, net_list_price=10, included=True
                )
            ],
            gross_list_price=5000.00,
            net_list_price=5000.00,
        )
        list_of_difference_item = [
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="4000.00",
                new_value="5000.00",
                reason=DifferenceReason.PRICE_CHANGE,
            ),
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="4000.00/10/10",
                new_value="5000.00/xyz",
                reason=DifferenceReason.OPTION_INCLUDED,
            ),
        ]
        expected_price_difference = [
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=4000.0,
                new_price=5000.00,
                perc_change="25%",
                model_price_change=1000.00,
                reason=PriceDifferenceReason.PRICE_INCREASE_OPTION_INCLUDED,
                option_code="xyz",
                option_net_list_price=10.0,
                option_gross_list_price=10.0,
            )
        ]

        actual = create_price_difference_item_with_merged_reason(
            list_of_difference_item
        )

        assert actual == expected_price_difference

    def test_create_price_difference_item_with_merged_reason_returns_price_difference_item_with_price_decrease_and_option_included_as_reasons_it_merges_the_reason(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            model_range_code="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="xyz", gross_list_price=10, net_list_price=10, included=True
                )
            ],
            gross_list_price=5000.00,
            net_list_price=5000.00,
        )
        list_of_difference_item = [
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="5000.00",
                new_value="4000.00",
                reason=DifferenceReason.PRICE_CHANGE,
            ),
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="5000.00/10/10",
                new_value="4000.00/xyz",
                reason=DifferenceReason.OPTION_INCLUDED,
            ),
        ]
        expected_price_difference = [
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=5000.0,
                new_price=4000.00,
                perc_change="20%",
                model_price_change=-1000.00,
                reason=PriceDifferenceReason.PRICE_DECREASE_OPTION_INCLUDED,
                option_code="xyz",
                option_net_list_price=10.0,
                option_gross_list_price=10.0,
            )
        ]

        actual = create_price_difference_item_with_merged_reason(
            list_of_difference_item
        )

        assert actual == expected_price_difference

    def test_create_price_difference_item_with_merged_reason_returns_price_difference_item_with_price_increase_and_option_excluded_as_reasons_it_merges_the_reason(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            model_range_code="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="xyz", gross_list_price=10, net_list_price=10, included=False
                )
            ],
            gross_list_price=5000.00,
            net_list_price=5000.00,
        )
        list_of_difference_item = [
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="4000.00",
                new_value="5000.00",
                reason=DifferenceReason.PRICE_CHANGE,
            ),
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="4000.00",
                new_value="5000.00/xyz",
                reason=DifferenceReason.OPTION_EXCLUDED,
            ),
        ]
        expected_price_difference = [
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=4000.0,
                new_price=5000.00,
                perc_change="25%",
                model_price_change=1000.00,
                reason=PriceDifferenceReason.PRICE_INCREASE_OPTION_EXCLUDED,
                option_code="xyz",
                option_net_list_price=0.0,
                option_gross_list_price=0.0,
            )
        ]

        actual = create_price_difference_item_with_merged_reason(
            list_of_difference_item
        )

        assert actual == expected_price_difference

    def test_create_price_difference_item_with_merged_reason_returns_price_difference_item_with_price_decrease_and_option_excluded_as_reasons_it_merges_the_reason(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            model_range_code="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="xyz", gross_list_price=10, net_list_price=10, included=True
                )
            ],
            gross_list_price=5000.00,
            net_list_price=5000.00,
        )
        list_of_difference_item = [
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="5000.00",
                new_value="4000.00",
                reason=DifferenceReason.PRICE_CHANGE,
            ),
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="5000.00",
                new_value="4000.00/xyz",
                reason=DifferenceReason.OPTION_EXCLUDED,
            ),
        ]
        expected_price_difference = [
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=5000.0,
                new_price=4000.00,
                perc_change="20%",
                model_price_change=-1000.00,
                reason=PriceDifferenceReason.PRICE_DECREASE_OPTION_EXCLUDED,
                option_code="xyz",
                option_net_list_price=0.0,
                option_gross_list_price=0.0,
            )
        ]

        actual = create_price_difference_item_with_merged_reason(
            list_of_difference_item
        )

        assert actual == expected_price_difference

    def test_create_price_difference_item_with_merged_reason_returns_price_difference_item_with_only_option_changes_as_reasons_it_merges_the_reason(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            model_range_code="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="abc", gross_list_price=10, net_list_price=10, included=False
                ),
                create_test_line_item_option_code(
                    code="xyz", gross_list_price=10, net_list_price=10, included=True
                ),
            ],
            gross_list_price=5000.00,
            net_list_price=5000.00,
        )
        list_of_difference_item = [
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="5000.00",
                new_value="5000.00/abc",
                reason=DifferenceReason.OPTION_EXCLUDED,
            ),
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="5000.00/10/10",
                new_value="5000.00/xyz",
                reason=DifferenceReason.OPTION_INCLUDED,
            ),
        ]
        expected_price_difference = [
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=5000.0,
                new_price=5000.00,
                perc_change="0%",
                model_price_change=0.00,
                reason=PriceDifferenceReason.OPTION_EXCLUDED,
                option_code="abc",
                option_net_list_price=0.0,
                option_gross_list_price=0.0,
            ),
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=5000.0,
                new_price=5000.00,
                perc_change="0%",
                model_price_change=0.00,
                reason=PriceDifferenceReason.OPTION_INCLUDED,
                option_code="xyz",
                option_net_list_price=10.0,
                option_gross_list_price=10.0,
            ),
        ]

        actual = create_price_difference_item_with_merged_reason(
            list_of_difference_item
        )

        assert actual == expected_price_difference

    def test_create_price_difference_item_with_merged_reason_returns_price_difference_item_with_price_increase_and_option_changes_as_reasons_it_merges_the_reason(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            model_range_code="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="abc", gross_list_price=10, net_list_price=10, included=False
                ),
                create_test_line_item_option_code(
                    code="xyz", gross_list_price=10, net_list_price=10, included=True
                ),
            ],
            gross_list_price=5000.00,
            net_list_price=5000.00,
        )
        list_of_difference_item = [
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="4000.00",
                new_value="5000.00",
                reason=DifferenceReason.PRICE_CHANGE,
            ),
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="4000.00",
                new_value="5000.00/abc",
                reason=DifferenceReason.OPTION_EXCLUDED,
            ),
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="4000.00/10/10",
                new_value="5000.00/xyz",
                reason=DifferenceReason.OPTION_INCLUDED,
            ),
        ]
        expected_price_difference = [
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=4000.0,
                new_price=5000.00,
                perc_change="25%",
                model_price_change=1000.00,
                reason=PriceDifferenceReason.PRICE_INCREASE_OPTION_INCLUDED,
                option_code="xyz",
                option_net_list_price=10.0,
                option_gross_list_price=10.0,
            ),
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=4000.0,
                new_price=5000.00,
                perc_change="25%",
                model_price_change=1000.00,
                reason=PriceDifferenceReason.PRICE_INCREASE_OPTION_EXCLUDED,
                option_code="abc",
                option_net_list_price=0.0,
                option_gross_list_price=0.0,
            ),
        ]

        actual = create_price_difference_item_with_merged_reason(
            list_of_difference_item
        )

        assert actual == expected_price_difference

    def test_create_price_difference_item_with_merged_reason_returns_price_difference_item_with_price_decrease_and_option_changes_as_reasons_it_merges_the_reason(
        self,
    ):
        line_item1_today = create_test_line_item(
            recorded_at=today_dashed_str_with_key(),
            model_range_code="model_1",
            model_code="model_code_1",
            line_code="audi_cool_model",
            line_option_codes=[
                create_test_line_item_option_code(
                    code="abc", gross_list_price=10, net_list_price=10, included=False
                ),
                create_test_line_item_option_code(
                    code="xyz", gross_list_price=10, net_list_price=10, included=True
                ),
            ],
            gross_list_price=4000.00,
            net_list_price=4000.00,
        )
        list_of_difference_item = [
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="5000.00",
                new_value="4000.00",
                reason=DifferenceReason.PRICE_CHANGE,
            ),
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="5000.00",
                new_value="4000.00/abc",
                reason=DifferenceReason.OPTION_EXCLUDED,
            ),
            create_difference_line_item(
                recorded_at=today_dashed_str_with_key(),
                model_range_code="model_1",
                model_code="model_code_1",
                line_code="audi_cool_model",
                old_value="5000.00/10/10",
                new_value="4000.00/xyz",
                reason=DifferenceReason.OPTION_INCLUDED,
            ),
        ]
        expected_price_difference = [
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=5000.0,
                new_price=4000.00,
                perc_change="20%",
                model_price_change=-1000.00,
                reason=PriceDifferenceReason.PRICE_DECREASE_OPTION_INCLUDED,
                option_code="xyz",
                option_net_list_price=10.0,
                option_gross_list_price=10.0,
            ),
            create_test_difference_item(
                line_item=line_item1_today,
                old_price=5000.0,
                new_price=4000.00,
                perc_change="20%",
                model_price_change=-1000.00,
                reason=PriceDifferenceReason.PRICE_DECREASE_OPTION_EXCLUDED,
                option_code="abc",
                option_net_list_price=0.0,
                option_gross_list_price=0.0,
            ),
        ]

        actual = create_price_difference_item_with_merged_reason(
            list_of_difference_item
        )

        assert actual == expected_price_difference

    def test_create_price_difference_item_with_merged_reason_returns_empty_list_when_an_empty_difference_item_list_is_given(
        self,
    ):
        list_of_difference_item = []
        expected_price_difference = []

        actual = create_price_difference_item_with_merged_reason(
            list_of_difference_item
        )

        assert actual == expected_price_difference

    def test_difference_with_when_only_option_code_is_changed_then_should_not_detect_as_option_added(
        self,
    ):
        prev_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        current_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BR1",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        assert (
            check_item_differences(current=current_dataset, previous=prev_dataset)[0]
            == []
        )

    def test_difference_with_when_only_option_description_is_changed_then_should_not_detect_as_option_added(
        self,
    ):
        prev_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        current_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="New Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        assert (
            check_item_differences(current=current_dataset, previous=prev_dataset)[0]
            == []
        )

    def test_difference_with_when_only_option_code_is_changed_then_should_not_detect_as_option_removed(
        self,
    ):
        prev_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="TMP",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        current_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        assert (
            check_item_differences(current=current_dataset, previous=prev_dataset)[0]
            == []
        )

    def test_difference_with_when_only_option_description_is_changed_then_should_not_detect_as_option_removed(
        self,
    ):
        prev_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="New Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        current_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="Brakes",
                        net_list_price=0,
                        gross_list_price=0,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        assert (
            check_item_differences(current=current_dataset, previous=prev_dataset)[0]
            == []
        )

    def test_option_price_change_when_options_price_increases(self):
        prev_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="New Brakes",
                        net_list_price=100,
                        gross_list_price=200,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        current_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="New Brakes",
                        net_list_price=200,
                        gross_list_price=300,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        actual = check_item_differences(current=current_dataset, previous=prev_dataset)
        expected = (
            [
                DifferenceItem(
                    recorded_at=today_dashed_str(),
                    vendor=Vendor.TESLA,
                    series="Model Test",
                    model_range_code="XFA3",
                    model_range_description="R Coupe",
                    model_code="MS22",
                    model_description="R3",
                    line_code="SP",
                    line_description="Sport",
                    old_value='{"option_description":"New '
                    'Brakes","old_price":"100"}',
                    new_value="200",
                    reason=DifferenceReason.OPTION_PRICE_CHANGE,
                    market=Market.AU,
                )
            ],
            [],
            [
                OptionPriceDifferenceItem(
                    recorded_at=today_dashed_str(),
                    vendor=Vendor.TESLA,
                    market=Market.AU,
                    option_description="New Brakes",
                    option_old_price=100.0,
                    option_new_price=200.0,
                    currency="AUD",
                    perc_change="100%",
                    option_price_change=100.0,
                    reason=OptionPriceDifferenceReason.PRICE_INCREASE,
                    model_range_description="R Coupe",
                )
            ],
        )

        assert actual == expected

    def test_option_price_change_when_options_price_decreases(self):
        prev_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="New Brakes",
                        net_list_price=200,
                        gross_list_price=300,
                        included=True,
                    ),
                ]
            )
            .build()
        ]

        current_dataset = [
            LineItemBuilder()
            .with_line_option_code(
                [
                    LineItemOptionCode(
                        code="BRK",
                        type="brake",
                        description="New Brakes",
                        net_list_price=100,
                        gross_list_price=200,
                        included=True,
                    ),
                ]
            )
            .build()
        ]
        assert check_item_differences(current=current_dataset, previous=prev_dataset)[
            0
        ] == [
            build_difference_for(
                line_item=LineItemBuilder().build(),
                reason=DifferenceReason.OPTION_PRICE_CHANGE,
                old_value='{"option_description":"New Brakes","old_price":"200"}',
                new_value="100",
            )
        ]

    def test_check_option_price_difference_return_option_price_difference_item_when_option_has_price_increase(
        self,
    ):
        dictionary_old_value = """
        {
            "option_description": "A1 option",
            "old_price": 10.0
        }
        """

        new_value = "20.0"

        difference_line_item = create_difference_line_item(
            market=Market.DE,
            vendor=Vendor.AUDI,
            reason=DifferenceReason.OPTION_PRICE_CHANGE,
            model_range_description="model_range",
            old_value=dictionary_old_value,
            new_value=new_value,
        )

        expected_option_price_difference = create_test_option_price_difference_item(
            vendor=Vendor.AUDI,
            market=Market.DE,
            option_old_price=10.0,
            option_new_price=20.0,
            perc_change="100%",
            option_price_change=10.0,
            reason=OptionPriceDifferenceReason.PRICE_INCREASE,
            option_description="A1 option",
            model_range_description="model_range",
            currency="EUR",
        )

        actual = create_option_price_difference_item([difference_line_item])
        assert actual[0] == expected_option_price_difference

    def test_check_option_price_difference_return_option_price_difference_item_when_option_has_price_decrease(
        self,
    ):
        dictionary_old_value = """
            {
                "option_description": "A1 option",
                "old_price": 20.0
            }
            """

        new_value = "10.0"

        difference_line_item = create_difference_line_item(
            market=Market.DE,
            vendor=Vendor.AUDI,
            reason=DifferenceReason.OPTION_PRICE_CHANGE,
            model_range_description="model_range",
            old_value=dictionary_old_value,
            new_value=new_value,
        )
        difference_line_item_2 = create_difference_line_item(
            market=Market.DE,
            vendor=Vendor.AUDI,
            reason=DifferenceReason.OPTION_PRICE_CHANGE,
            model_range_description="model_range",
            old_value="""
            {
                "option_description": "A1 option",
                "old_price": 10.0
            }
            """,
            new_value=new_value,
        )

        expected = create_test_option_price_difference_item(
            vendor=Vendor.AUDI,
            market=Market.DE,
            option_old_price=20.0,
            option_new_price=10.0,
            perc_change="-50%",
            option_price_change=-10.0,
            reason=OptionPriceDifferenceReason.PRICE_DECREASE,
            option_description="A1 option",
            model_range_description="model_range",
            currency="EUR",
        )

        actual = create_option_price_difference_item(
            [difference_line_item, difference_line_item_2]
        )

        assert actual == [expected]
