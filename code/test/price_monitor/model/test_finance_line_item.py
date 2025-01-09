from src.price_monitor.utils.clock import (
    yesterday_dashed_str_with_key,
    today_dashed_str,
)
from test.price_monitor.utils.test_data_builder import create_test_finance_line_item

from assertpy import assert_that

from src.price_monitor.model.finance_line_item import (
    FinanceLineItem,
    create_finance_line_item,
)
from src.price_monitor.model.vendor import Market, Vendor


def test_create_financial_line_item():
    expected_finance_line_item = create_test_finance_line_item()
    actual_finance_line_item = create_finance_line_item(
        vendor=Vendor.AUDI,
        market=Market.DE,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        contract_type="test",
        monthly_rental_nlp=0.0,
        monthly_rental_glp=0.0,
    )

    assert expected_finance_line_item == actual_finance_line_item


def test_cannot_create_item_with_blank_market():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="abc",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        market=" ",
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_blank_series():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series=" ",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_blank_model_range_code():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code=" ",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_blank_model_range_description():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description=" ",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_blank_model_code():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code=" ",
        model_description="test",
        line_code="test",
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_blank_model_description():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description=" ",
        line_code="test",
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_blank_line_code():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code=" ",
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_blank_line_description():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description=" ",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_blank_contract_type():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="Abv",
        market=Market.DE,
        currency="USD",
        contract_type=" ",
    )


def test_cannot_create_item_with_missing_vendor():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=None,
        series="abc",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_missing_market():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="abc",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        market=None,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_missing_series():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series=None,
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_missing_model_range_code():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code=None,
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_missing_model_range_description():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description=None,
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_missing_model_code():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code=None,
        model_description="test",
        line_code="test",
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_missing_model_description():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description=None,
        line_code="test",
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_missing_line_code():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code=None,
        line_description="test",
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_missing_line_description():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description=None,
        market=Market.DE,
        currency="USD",
        contract_type="test",
    )


def test_cannot_create_item_with_missing_contract_type():
    assert_that(FinanceLineItem).raises(ValueError).when_called_with(
        recorded_at="test",
        vendor=Vendor.AUDI,
        series="test",
        model_range_code="test",
        model_range_description="test",
        model_code="test",
        model_description="test",
        line_code="test",
        line_description="Abv",
        market=Market.DE,
        currency="USD",
        contract_type=None,
    )


def test_vehicle_id_is_unique_for_two_models():
    finance_item1 = create_test_finance_line_item(
        vendor=Vendor.AUDI,
        market=Market.UK,
        series="series1",
        model_range_description="model_range1",
        model_description="model1",
        line_description="line1",
    )

    vehicle_id_1 = finance_item1.calculate_vehicle_id()

    finance_item2 = create_test_finance_line_item(
        vendor=Vendor.AUDI,
        market=Market.UK,
        series="series2",
        model_range_description="model_range2",
        model_description="model2",
        line_description="line2",
    )
    vehicle_id_2 = finance_item2.calculate_vehicle_id()

    assert vehicle_id_1 != vehicle_id_2


def test_vehicle_id_is_unique_for_multiple_models_under_all_vendors():
    list_of_all_vehicle_ids = []
    list_of_all_vehicle_ids.extend(
        [
            create_test_finance_line_item(
                vendor=Vendor.AUDI,
                market=Market.UK,
                series="e-tron GT",
                model_range_description="e-tron GT quattro",
                model_description="e-tron GT quattro Vorsprung 60 quattro",
                line_description="VORSPRUNG",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.AUDI,
                market=Market.UK,
                series="A1",
                model_range_description="A1 Sportback",
                model_description="Black Edition 30 TFSI S tronic",
                line_description="BLACK_EDITION",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.AUDI,
                market=Market.UK,
                series="A1",
                model_range_description="A1 Sportback",
                model_description="S line 25 TFSI S tronic",
                line_description="SLINE",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.AUDI,
                market=Market.UK,
                series="A7",
                model_range_description="A7 Sportback",
                model_description="Black Edition 40 TDI quattro S tronic",
                line_description="BLACK_EDITION",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.AUDI,
                market=Market.UK,
                series="A7",
                model_range_description="S7 Sportback",
                model_description="Vorsprung TDI quattro tiptronic",
                line_description="VORSPRUNG",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.AUDI,
                market=Market.UK,
                series="A8",
                model_range_description="A8",
                model_description="Vorsprung TDI quattro tiptronic",
                line_description="VORSPRUNG",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.AUDI,
                market=Market.UK,
                series="Q2",
                model_range_description="Q2",
                model_description="S line 35 TFSI 6-speed",
                line_description="SLINE",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.BMW,
                market=Market.UK,
                series="1",
                model_range_description="BMW 1 Series",
                model_description="BMW M135 xDrive - automatic",
                line_description="M_PERFORMANCE_LINE",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.BMW,
                market=Market.UK,
                series="3",
                model_range_description="BMW 3 Series Saloon",
                model_description="BMW 320i M Sport Saloon - automatic",
                line_description="M Sport",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.BMW,
                market=Market.UK,
                series="4",
                model_range_description="BMW 4 Series Convertible",
                model_description="BMW 420i M Sport Convertible - automatic",
                line_description="M Sport",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.BMW,
                market=Market.UK,
                series="7",
                model_range_description="BMW 7 Series Saloon",
                model_description="BMW i7 xDrive60 Excellence Pro - automatic",
                line_description="BASIC_LINE",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.BMW,
                market=Market.UK,
                series="8",
                model_range_description="BMW 8 Series Coup√©",
                model_description="BMW M850i xDrive Coup√© - automatic",
                line_description="M_PERFORMANCE_LINE",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.BMW,
                market=Market.UK,
                series="I",
                model_range_description="BMW i7",
                model_description="BMW i7 eDrive50 M Sport - automatic",
                line_description="M Sport",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.BMW,
                market=Market.UK,
                series="M",
                model_range_description="BMW M4 Convertible",
                model_description="BMW M4 Competition Convertible with M xDrive - automatic",
                line_description="M_PERFORMANCE_LINE",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.TESLA,
                market=Market.UK,
                series="m3",
                model_range_description="Model 3",
                model_description="Model 3",
                line_description="Performance",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.TESLA,
                market=Market.UK,
                series="m3",
                model_range_description="Model 3",
                model_description="Model 3",
                line_description="Rear-Wheel Drive",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.TESLA,
                market=Market.UK,
                series="my",
                model_range_description="Model Y",
                model_description="Model Y",
                line_description="Long Range AWD",
            ).calculate_vehicle_id(),
            create_test_finance_line_item(
                vendor=Vendor.TESLA,
                market=Market.UK,
                series="my",
                model_range_description="Model Y",
                model_description="Model Y",
                line_description="Rear-Wheel Drive",
            ).calculate_vehicle_id(),
        ]
    )
    print(list_of_all_vehicle_ids)

    assert len(list_of_all_vehicle_ids) == len(set(list_of_all_vehicle_ids))


def test_is_current_when_last_scraped_on_is_today():
    line_item = create_test_finance_line_item(last_scraped_on=today_dashed_str())
    assert_that(line_item).has_is_current(True)


def test_is_not_current_when_date_and_last_scraped_is_not_today():
    line_item = create_test_finance_line_item(
        last_scraped_on=yesterday_dashed_str_with_key()
    )
    assert_that(line_item).has_is_current(False)


def test_unknown_is_current_when_last_scraped_on_is_missing():
    line_item = create_test_finance_line_item(last_scraped_on=None)
    assert_that(line_item).has_is_current(None)
