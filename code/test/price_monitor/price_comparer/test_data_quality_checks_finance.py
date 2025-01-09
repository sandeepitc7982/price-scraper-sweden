import unittest
from test.price_monitor.utils.test_data_builder import create_test_finance_line_item
from unittest.mock import Mock, call, patch

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.data_quality.data_quality_checks_finance import (
    DataQualityCheckFinance,
)
from src.price_monitor.utils.clock import today_dashed_str_with_key


class TestDataQualityCheckFinances(unittest.TestCase):
    @patch("src.price_monitor.data_quality.data_quality_checks_finance.logger")
    def test_data_quality_check_calls_the_logger_when_zero_model_loaded(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks_finance = DataQualityCheckFinance(mock_repository)
        mock_repository.load_market.return_value = []
        data_quality_checks_finance.run_check_for_vendor_and_market(
            vendor=Vendor.TESLA, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with("[US-tesla] Zero Models Found")
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.TESLA,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks_finance.logger")
    def test_data_quality_check_calls_the_logger_when_monthly_glp_is_negative(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks_finance = DataQualityCheckFinance(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_finance_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                monthly_rental_glp=-413,
                model_range_description="range_desc",
                model_description="model_desc",
                line_description="line_desc",
                number_of_installments=3,
                term_of_agreement=6,
            )
        ]
        data_quality_checks_finance.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] Negative Monthly Rental GLP for model_range:range_desc model_description:model_desc line_description:line_desc"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks_finance.logger")
    def test_data_quality_check_calls_the_logger_when_monthly_nlp_is_negative(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks_finance = DataQualityCheckFinance(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_finance_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                monthly_rental_nlp=-400,
                model_range_description="range_desc",
                model_description="model_desc",
                line_description="line_desc",
                number_of_installments=3,
                term_of_agreement=6,
            )
        ]
        data_quality_checks_finance.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] Negative Monthly Rental NLP for model_range:range_desc model_description:model_desc line_description:line_desc"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks_finance.logger")
    def test_data_quality_check_calls_the_logger_when_model_range_description_contains_new_line_character(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks_finance = DataQualityCheckFinance(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_finance_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                model_range_description="A4 \n Sportsback",
                model_description="model",
                line_description="line",
                number_of_installments=3,
                term_of_agreement=6,
            )
        ]
        data_quality_checks_finance.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] New Line Character Error in Model_Range_Description for model_range:A4 \n Sportsback model_description:model line_description:line"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks_finance.logger")
    def test_data_quality_check_calls_the_logger_when_model_description_contains_new_line_character(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks_finance = DataQualityCheckFinance(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_finance_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                model_range_description="model range",
                model_description="A4 \n Avant",
                line_description="line",
                number_of_installments=3,
                term_of_agreement=6,
            )
        ]
        data_quality_checks_finance.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] New Line Character Error in Model_Description for model_range:model range model_description:A4 \n Avant line_description:line"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks_finance.logger")
    def test_data_quality_check_calls_the_logger_when_line_description_contains_new_line_character(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks_finance = DataQualityCheckFinance(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_finance_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                model_range_description="model range",
                model_description="model description",
                line_description="A4 \n Sportsback",
                number_of_installments=3,
                term_of_agreement=6,
            )
        ]
        data_quality_checks_finance.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] New Line Character Error in Line_Description for model_range:model range model_description:model description line_description:A4 \n Sportsback"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks_finance.logger")
    def test_check_for_check_for_model_duplication(self, mock_logger):
        mock_repository = Mock()
        data_quality_checks_finance = DataQualityCheckFinance(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_finance_line_item(
                vendor=Vendor.AUDI,
                market=Market.DE,
                series="series",
                model_range_code="model range code",
                model_range_description="model range",
                model_code="model code",
                model_description="model",
                line_code="line code",
                line_description="line",
                contract_type="type",
                number_of_installments=3,
                term_of_agreement=6,
            ),
            create_test_finance_line_item(
                vendor=Vendor.AUDI,
                market=Market.DE,
                series="series",
                model_range_code="model range code",
                model_range_description="model range",
                model_code="model code",
                model_description="model",
                line_code="line code",
                line_description="line",
                contract_type="type",
                number_of_installments=3,
                term_of_agreement=6,
            ),
        ]
        data_quality_checks_finance.run_check_for_vendor_and_market(
            vendor=Vendor.AUDI, markets=[Market.DE]
        )

        mock_logger.warning.assert_has_calls(
            [
                call("[DE-audi] Duplication of Models Found"),
                call(
                    "series # model range code # model range # model code # model # line code # line # type\n"
                ),
            ]
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks_finance.logger")
    def test_check_for_number_of_instalments_higher_than_zero_when_zero_then_log_it(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks_finance = DataQualityCheckFinance(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_finance_line_item(
                vendor=Vendor.AUDI,
                market=Market.DE,
                series="series",
                model_range_code="model range code",
                model_range_description="model range",
                model_code="model code",
                model_description="model",
                line_code="line code",
                line_description="line",
                contract_type="PCP",
                number_of_installments=0,
            )
        ]
        data_quality_checks_finance.run_check_for_vendor_and_market(
            vendor=Vendor.AUDI, markets=[Market.DE]
        )

        mock_logger.warning.assert_called_with(
            "[DE-audi] No. of Installments Zero for model_range:model range model_description:model line_description:line"
        )

    @patch("src.price_monitor.data_quality.data_quality_checks_finance.logger")
    def test_check_for_no_of_installments_not_higher_than_contract_duration_when_greater_then_log_it(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks_finance = DataQualityCheckFinance(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_finance_line_item(
                vendor=Vendor.AUDI,
                market=Market.DE,
                series="series",
                model_range_code="model range code",
                model_range_description="model range",
                model_code="model code",
                model_description="model",
                line_code="line code",
                line_description="line",
                contract_type="PCP",
                number_of_installments=6,
                term_of_agreement=5,
            )
        ]
        data_quality_checks_finance.run_check_for_vendor_and_market(
            vendor=Vendor.AUDI, markets=[Market.DE]
        )

        mock_logger.warning.assert_called_with(
            "[DE-audi] No. of installments is greater then contract duration for model_range:model range model_description:model line_description:line"
        )

    @patch.object(
        DataQualityCheckFinance,
        "_check_for_no_of_installments_not_higher_than_contract_duration",
    )
    @patch.object(
        DataQualityCheckFinance, "_check_for_number_of_instalments_higher_than_zero"
    )
    @patch("src.price_monitor.data_quality.data_quality_checks_finance.logger")
    def test_assert_output_when_contract_type_pcp_then_run_no_of_installment_checks(
        self,
        mock_logger,
        mock__check_for_number_of_instalments_higher_than_zero,
        mock__check_for_no_of_installments_not_higher_than_contract_duration,
    ):
        mock_repository = Mock()
        data_quality_checks_finance = DataQualityCheckFinance(mock_repository)
        line_item = create_test_finance_line_item(
            vendor=Vendor.AUDI,
            market=Market.DE,
            series="series",
            model_range_code="model range code",
            model_range_description="model range",
            model_code="model code",
            model_description="model",
            line_code="line code",
            line_description="line",
            contract_type="PCP",
            number_of_installments=0,
        )
        mock_repository.load_market.return_value = [
            line_item,
            create_test_finance_line_item(contract_type="PCH"),
        ]
        data_quality_checks_finance.run_check_for_vendor_and_market(
            vendor=Vendor.AUDI, markets=[Market.DE]
        )

        assert 1 == mock__check_for_number_of_instalments_higher_than_zero.call_count
        assert (
            1
            == mock__check_for_no_of_installments_not_higher_than_contract_duration.call_count
        )
        mock__check_for_number_of_instalments_higher_than_zero.assert_called_with(
            line_item
        )
        mock__check_for_no_of_installments_not_higher_than_contract_duration.assert_called_with(
            line_item
        )
