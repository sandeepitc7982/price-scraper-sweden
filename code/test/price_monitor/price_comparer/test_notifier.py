from test.price_monitor.builder.line_item_builder import LineItemBuilder
from test.price_monitor.utils.test_data_builder import create_difference_line_item

from src.price_monitor.model.difference_item import (
    DifferenceReason,
    build_difference_for,
)
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.notifier.notifier import (
    _summarize_differences,
    _summarize_model_price_change,
)


def test_summary():
    differences = [
        build_difference_for(
            LineItemBuilder().with_vendor(Vendor.BMW).with_market(Market.DE).build(),
            DifferenceReason.NEW_LINE,
        ),
        build_difference_for(
            LineItemBuilder().with_vendor(Vendor.BMW).with_market(Market.DE).build(),
            DifferenceReason.NEW_LINE,
        ),
        build_difference_for(
            LineItemBuilder().with_vendor(Vendor.BMW).with_market(Market.DE).build(),
            DifferenceReason.PRICE_CHANGE,
        ),
        build_difference_for(
            LineItemBuilder().with_vendor(Vendor.AUDI).with_market(Market.FR).build(),
            DifferenceReason.PRICE_CHANGE,
        ),
        build_difference_for(
            LineItemBuilder().with_vendor(Vendor.AUDI).with_market(Market.FR).build(),
            DifferenceReason.PRICE_CHANGE,
        ),
        build_difference_for(
            LineItemBuilder().with_vendor(Vendor.AUDI).with_market(Market.DE).build(),
            DifferenceReason.LINE_REMOVED,
        ),
        build_difference_for(
            LineItemBuilder().with_vendor(Vendor.AUDI).with_market(Market.DE).build(),
            DifferenceReason.LINE_REMOVED,
        ),
        build_difference_for(
            LineItemBuilder().with_vendor(Vendor.AUDI).with_market(Market.DE).build(),
            DifferenceReason.NEW_LINE,
        ),
        build_difference_for(
            LineItemBuilder().with_vendor(Vendor.TESLA).with_market(Market.NL).build(),
            DifferenceReason.OPTION_ADDED,
        ),
        build_difference_for(
            LineItemBuilder().with_vendor(Vendor.TESLA).with_market(Market.NL).build(),
            DifferenceReason.OPTION_REMOVED,
        ),
        build_difference_for(
            LineItemBuilder().with_vendor(Vendor.TESLA).with_market(Market.AU).build(),
            DifferenceReason.OPTION_REMOVED,
        ),
    ]

    summary = _summarize_differences(differences)

    assert summary == {
        Vendor.BMW: {
            Market.DE: {DifferenceReason.NEW_LINE: 2, DifferenceReason.PRICE_CHANGE: 1}
        },
        Vendor.AUDI: {
            Market.FR: {
                DifferenceReason.PRICE_CHANGE: 2,
            },
            Market.DE: {
                DifferenceReason.LINE_REMOVED: 2,
                DifferenceReason.NEW_LINE: 1,
            },
        },
        Vendor.TESLA: {
            Market.NL: {
                DifferenceReason.OPTION_ADDED: 1,
                DifferenceReason.OPTION_REMOVED: 1,
            },
            Market.AU: {
                DifferenceReason.OPTION_REMOVED: 1,
            },
        },
    }


def test_summary_model_price_change():
    line_description = "basic line"
    line_code = "code basic line"
    line_description_1 = "line_description"
    price_diff = build_difference_for(
        line_item=LineItemBuilder()
        .with_vendor(Vendor.BMW)
        .with_market(Market.DE)
        .with_line_description(line_description)
        .with_line_code(line_code)
        .with_gross_list_price(8000)
        .with_currency("eur")
        .build(),
        reason=DifferenceReason.PRICE_CHANGE,
        old_value="10000",
        new_value="8000",
    )
    price_diff_1 = build_difference_for(
        line_item=LineItemBuilder()
        .with_vendor(Vendor.BMW)
        .with_market(Market.DE)
        .with_line_description(line_description_1)
        .with_line_code("line code")
        .with_gross_list_price(10000)
        .with_currency("eur")
        .build(),
        reason=DifferenceReason.PRICE_CHANGE,
        old_value="8000",
        new_value="10000",
    )
    price_diff_2 = build_difference_for(
        line_item=LineItemBuilder()
        .with_vendor(Vendor.BMW)
        .with_market(Market.UK)
        .with_line_description(line_description_1)
        .with_line_code("line code")
        .with_gross_list_price(10000)
        .with_currency("gbp")
        .build(),
        reason=DifferenceReason.PRICE_CHANGE,
        old_value="8000",
        new_value="10000",
    )

    actual = _summarize_model_price_change([price_diff, price_diff_1, price_diff_2])

    expected_summary = {
        "bmw": {
            "DE": [
                {
                    "% OF CHANGE": "-20.0% ↓",
                    "MODEL NAME": "R3 basic line",
                    "OLD PRICE": "10,000.0 €",
                    "NEW PRICE": "8,000.0 €",
                },
                {
                    "% OF CHANGE": "25.0% ↑",
                    "MODEL NAME": "R3 line_description",
                    "OLD PRICE": "8,000.0 €",
                    "NEW PRICE": "10,000.0 €",
                },
            ],
            "UK": [
                {
                    "% OF CHANGE": "25.0% ↑",
                    "MODEL NAME": "R3 line_description",
                    "OLD PRICE": "8,000.0 £",
                    "NEW PRICE": "10,000.0 £",
                }
            ],
        }
    }

    assert actual == expected_summary


def test_summary_counts_only_unique_options_added_for_multiple_series_to_summarize_the_message():
    differences = [
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            line_description="Line1",
            new_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series3",
            line_description="Line2",
            new_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series2",
            line_description="Line2",
            new_value="Option_code2/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
    ]

    summary = _summarize_differences(differences)

    assert summary == {
        Vendor.TESLA: {
            Market.DE: {
                DifferenceReason.OPTION_ADDED: 2,
            },
        },
    }


def test_summary_counts_only_unique_options_removed_for_multiple_series_to_summarize_the_message():
    differences = [
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            line_description="Line1",
            old_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series2",
            line_description="Line2",
            old_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series3",
            line_description="Line2",
            old_value="Option_code2/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
    ]

    summary = _summarize_differences(differences)

    assert summary == {
        Vendor.TESLA: {
            Market.DE: {
                DifferenceReason.OPTION_REMOVED: 2,
            },
        },
    }


def test_summary_counts_only_unique_options_added_for_one_series_to_summarize_the_message():
    differences = [
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            line_description="Line1",
            new_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            line_description="Line2",
            new_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            line_description="Line2",
            new_value="Option_code2/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
    ]

    summary = _summarize_differences(differences)

    assert summary == {
        Vendor.TESLA: {
            Market.DE: {
                DifferenceReason.OPTION_ADDED: 2,
            },
        },
    }


def test_summary_counts_only_unique_options_removed_for_one_series_to_summarize_the_message():
    differences = [
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            line_description="Line1",
            old_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            line_description="Line2",
            old_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            line_description="Line2",
            old_value="Option_code2/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
    ]

    summary = _summarize_differences(differences)

    assert summary == {
        Vendor.TESLA: {
            Market.DE: {
                DifferenceReason.OPTION_REMOVED: 2,
            },
        },
    }


def test_summary_counts_only_unique_options_added_for_multiple_model_ranges_to_summarize_the_message():
    differences = [
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            line_description="Line1",
            new_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description2",
            line_description="Line2",
            new_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description2",
            line_description="Line2",
            new_value="Option_code2/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
    ]

    summary = _summarize_differences(differences)

    assert summary == {
        Vendor.TESLA: {
            Market.DE: {
                DifferenceReason.OPTION_ADDED: 2,
            },
        },
    }


def test_summary_counts_only_unique_options_removed_for_multiple_model_ranges_to_summarize_the_message():
    differences = [
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            line_description="Line1",
            old_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description2",
            line_description="Line2",
            old_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description2",
            line_description="Line2",
            old_value="Option_code2/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
    ]

    summary = _summarize_differences(differences)

    assert summary == {
        Vendor.TESLA: {
            Market.DE: {
                DifferenceReason.OPTION_REMOVED: 2,
            },
        },
    }


def test_summary_counts_only_unique_options_added_for_a_model_to_summarize_the_message():
    differences = [
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            model_description="model_description1",
            line_description="Line1",
            new_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            model_description="model_description1",
            line_description="Line2",
            new_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            model_description="model_description1",
            line_description="Line2",
            new_value="Option_code2/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
    ]

    summary = _summarize_differences(differences)

    assert summary == {
        Vendor.TESLA: {
            Market.DE: {
                DifferenceReason.OPTION_ADDED: 2,
            },
        },
    }


def test_summary_counts_only_unique_options_removed_for_a_model_to_summarize_the_message():
    differences = [
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            model_description="model_description1",
            line_description="Line1",
            old_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            model_description="model_description1",
            line_description="Line2",
            old_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            model_description="model_description1",
            line_description="Line2",
            old_value="Option_code2/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
    ]

    summary = _summarize_differences(differences)

    assert summary == {
        Vendor.TESLA: {
            Market.DE: {
                DifferenceReason.OPTION_REMOVED: 2,
            },
        },
    }


def test_summary_counts_only_unique_options_added_for_a_line_to_summarize_the_message():
    differences = [
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            model_description="model_description1",
            line_description="Line1",
            new_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            model_description="model_description1",
            line_description="Line1",
            new_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            model_description="model_description1",
            line_description="Line1",
            new_value="Option_code2/Description",
            reason=DifferenceReason.OPTION_ADDED,
        ),
    ]

    summary = _summarize_differences(differences)

    assert summary == {
        Vendor.TESLA: {
            Market.DE: {
                DifferenceReason.OPTION_ADDED: 2,
            },
        },
    }


def test_summary_counts_only_unique_options_removed_for_a_line_to_summarize_the_message():
    differences = [
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            model_description="model_description1",
            line_description="Line1",
            old_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            model_description="model_description1",
            line_description="Line1",
            old_value="Option_code1/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
        create_difference_line_item(
            vendor=Vendor.TESLA,
            market=Market.DE,
            series="series1",
            model_range_description="model_range_description1",
            model_description="model_description1",
            line_description="Line1",
            old_value="Option_code2/Description",
            reason=DifferenceReason.OPTION_REMOVED,
        ),
    ]

    summary = _summarize_differences(differences)

    assert summary == {
        Vendor.TESLA: {
            Market.DE: {
                DifferenceReason.OPTION_REMOVED: 2,
            },
        },
    }
