from src.price_monitor.utils.clock import (
    yesterday_dashed_str_with_key,
    today_dashed_str,
)
from test.price_monitor.utils.test_data_builder import (
    create_difference_line_item,
    create_test_line_item,
    create_test_line_item_option_code,
)

from assertpy import assert_that

from src.price_monitor.model.difference_item import DifferenceReason
from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.vendor import Market, Vendor


def test_difference_with_calls_build_difference_for_when_net_list_price_differs_for_usa():
    line_item_original = create_test_line_item(
        net_list_price=10000.0,
        market=Market.US,
        model_code="A1A",
        line_option_codes=[
            create_test_line_item_option_code(
                code="A1",
                net_list_price=2000.0,
                description="A1 option",
                included=True,
            )
        ],
    )
    line_item2 = create_test_line_item(
        model_code="A1A",
        net_list_price=10000.0,
        market=Market.US,
        line_option_codes=[
            create_test_line_item_option_code(
                code="A1",
                net_list_price=2000.0,
                description="A1 option",
                included=False,
            )
        ],
    )

    actual = line_item_original.difference_with(line_item2)
    expected = [
        create_difference_line_item(
            vendor=Vendor.AUDI,
            model_range_description="test",
            model_code="A1A",
            model_description="test",
            line_code="test",
            line_description="test",
            old_value="10000.0/0.0/2000.0",
            new_value="10000.0/A1",
            reason=DifferenceReason.OPTION_INCLUDED,
            market=Market.US,
        ),
    ]

    assert actual == expected


def test_check_differences_for_option_price_change():
    line_item = create_test_line_item(
        model_code="A1A",
        line_option_codes=[
            create_test_line_item_option_code(
                code="A1",
                net_list_price=2000.0,
                description='50,8 cm (20") AMG Leichtmetallräder im Vielspeichen-Design',
            )
        ],
    )
    other_line_item = create_test_line_item(
        model_code="A1A",
        line_option_codes=[
            create_test_line_item_option_code(
                code="A1",
                net_list_price=3000.0,
                description='50,8 cm (20") AMG Leichtmetallräder im Vielspeichen-Design',
            )
        ],
    )

    actual_option_price_diff = line_item.check_differences_for_option_price_change(
        other_line_item
    )

    expected = create_difference_line_item(
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="A1A",
        model_description="test",
        line_code="test",
        line_description="test",
        old_value='{"option_description":"50,8 cm (20 inch) AMG Leichtmetallräder im Vielspeichen-Design","old_price":"3000.0"}',
        new_value="2000.0",
        reason=DifferenceReason.OPTION_PRICE_CHANGE,
        market=Market.NL,
    )

    assert actual_option_price_diff == [expected]


def test_check_differences_for_options_inclusion():
    line_item = create_test_line_item(
        model_code="A1A",
        line_option_codes=[create_test_line_item_option_code(code="A1", included=True)],
    )
    other_line_item = create_test_line_item(
        model_code="A1A",
        line_option_codes=[
            create_test_line_item_option_code(code="A1", included=False)
        ],
    )

    actual_option_price_diff = line_item.check_differences_for_options_inclusion(
        other_line_item
    )

    expected = create_difference_line_item(
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="A1A",
        model_description="test",
        line_code="test",
        line_description="test",
        old_value="0.0/0.0/0.0",
        new_value="0.0/A1",
        reason=DifferenceReason.OPTION_INCLUDED,
        market=Market.NL,
    )

    assert actual_option_price_diff == [expected]


def test_cannot_create_line_item_with_blank_market():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        market=" ",
        vendor=Vendor.AUDI,
        series="a3",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_blank_vendor():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        market=Market.UK,
        vendor=" ",
        series="a3",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_blank_series():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series=" ",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_blank_model_range_code():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code=" ",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_blank_model_range_description():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description=" ",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_blank_model_code():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code=" ",
        model_description="test",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_blank_model_description():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description=" ",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_blank_line_code():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code=" ",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_blank_line_description():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description=" ",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_missing_market():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        market=None,
        vendor=Vendor.AUDI,
        series="a3",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_missing_vendor():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        market=Market.UK,
        vendor=None,
        series="a3",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_missing_series():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series=None,
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_missing_model_range_code():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code=None,
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_missing_model_range_description():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description=None,
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_missing_model_code():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code=None,
        model_description="test",
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_missing_model_description():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description=None,
        line_code="test",
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_missing_line_code():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code=None,
        line_description="test",
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_cannot_create_line_item_with_missing_line_description():
    assert_that(LineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description=None,
        line_option_codes=[],
        net_list_price=10,
        gross_list_price=10,
        currency="USD",
    )


def test_is_current_when_last_scraped_on_is_today():
    line_item = create_test_line_item(last_scraped_on=today_dashed_str())
    assert_that(line_item).has_is_current(True)


def test_is_not_current_when_date_and_last_scraped_is_not_today():
    line_item = create_test_line_item(last_scraped_on=yesterday_dashed_str_with_key())
    assert_that(line_item).has_is_current(False)


def test_unknown_is_current_when_last_scraped_on_is_missing():
    line_item = create_test_line_item(last_scraped_on=None)
    assert_that(line_item).has_is_current(None)
