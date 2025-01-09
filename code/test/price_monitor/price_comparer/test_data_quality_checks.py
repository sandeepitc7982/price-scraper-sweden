import unittest
from test.price_monitor.utils.test_data_builder import (
    create_test_line_item,
    create_test_line_item_option_code,
)
from unittest.mock import Mock, patch

from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.data_quality.data_quality_checks import DataQualityCheck
from src.price_monitor.utils.clock import today_dashed_str_with_key


class TestDataQualityChecks(unittest.TestCase):
    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_mercedes_benz_data_quality_check_calls_the_logger_when_zero_model_loaded(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = []
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with("[US-mercedes_benz] Zero Models Found")
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_mercedes_benz_data_quality_check_calls_the_logger_when_model_gross_list_price_is_less_than_zero(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                gross_list_price=-15,
                line_option_codes=[
                    create_test_line_item_option_code(included=True),
                    create_test_line_item_option_code(included=False),
                ],
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] Model Negative Gross List Price"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_mercedes_benz_data_quality_check_calls_the_logger_when_model_net_list_price_is_less_than_zero(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                net_list_price=-15,
                line_option_codes=[
                    create_test_line_item_option_code(included=True),
                    create_test_line_item_option_code(included=False),
                ],
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] Model Negative Net List Price"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_mercedes_benz_data_quality_check_calls_the_logger_when_option_gross_list_price_is_less_than_zero(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                line_option_codes=[
                    create_test_line_item_option_code(
                        included=True, gross_list_price=-15
                    ),
                    create_test_line_item_option_code(included=False),
                ],
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] Option Negative Gross List Price"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_mercedes_benz_data_quality_check_calls_the_logger_when_option_net_list_price_is_less_than_zero(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                line_option_codes=[
                    create_test_line_item_option_code(
                        included=True, net_list_price=-15
                    ),
                    create_test_line_item_option_code(included=False),
                ],
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] Option Negative Net List Price"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_mercedes_benz_data_quality_check_calls_the_logger_when_model_range_description_contains_new_line_character(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                model_range_description="A4 \n Sportsback",
                model_description="model",
                line_description="line",
                line_option_codes=[
                    create_test_line_item_option_code(included=True),
                    create_test_line_item_option_code(included=False),
                ],
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
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

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_mercedes_benz_data_quality_check_calls_the_logger_when_model_description_contains_new_line_character(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                model_range_description="model range",
                model_description="A4 \n Avant",
                line_description="line",
                line_option_codes=[
                    create_test_line_item_option_code(included=True),
                    create_test_line_item_option_code(included=False),
                ],
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
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

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_mercedes_benz_data_quality_check_calls_the_logger_when_line_description_contains_new_line_character(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                model_range_description="model range",
                model_description="model description",
                line_description="A4 \n Sportsback",
                line_option_codes=[
                    create_test_line_item_option_code(included=True),
                    create_test_line_item_option_code(included=False),
                ],
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
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

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_mercedes_benz_data_quality_check_calls_the_logger_when_option_description_contains_new_line_character(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                line_option_codes=[
                    create_test_line_item_option_code(
                        included=True, description="I am \n option"
                    ),
                    create_test_line_item_option_code(included=False),
                ],
                model_description="model",
                model_range_description="model range",
                line_description="line",
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] New Line Character Error in Option_Description for model_range:model range model_description:model line_description:line"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_mercedes_benz_data_quality_check_calls_the_logger_when_option_inclusion_value_is_not_boolean(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                line_option_codes=[
                    create_test_line_item_option_code(included="This is a string"),
                    create_test_line_item_option_code(included=False),
                ],
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] Expected to be Boolean but Found <class 'str'>"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_mercedes_benz_data_quality_check_calls_the_logger_when_option_included_option_is_zero(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                line_option_codes=[
                    create_test_line_item_option_code(included=False),
                    create_test_line_item_option_code(included=False),
                ],
                model_description="model",
                model_range_description="model range",
                line_description="line",
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] Zero count of options included for options in model_range:model range model_description:model line_description:line"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_mercedes_benz_data_quality_check_calls_the_logger_when_option_excluded_option_is_zero(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        options = [
            create_test_line_item_option_code(
                code="code1", description="description1", included=True
            ),
            create_test_line_item_option_code(
                code="code1", description="description1", included=True
            ),
        ]
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.MERCEDES_BENZ,
                market=Market.US,
                line_option_codes=options,
                model_description="model",
                model_range_description="model range",
                line_description="line",
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.MERCEDES_BENZ, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-mercedes_benz] Zero count of options excluded for options in model_range:model range model_description:model line_description:line"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.MERCEDES_BENZ,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_audi_data_quality_check_calls_the_logger_when_zero_model_loaded(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = []
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.AUDI, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with("[US-audi] Zero Models Found")
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.AUDI,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_audi_data_quality_check_calls_the_logger_when_option_included_has_non_zero_price(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.AUDI,
                market=Market.US,
                line_option_codes=[
                    create_test_line_item_option_code(
                        gross_list_price=100, included=True
                    ),
                    create_test_line_item_option_code(included=False),
                ],
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.AUDI, markets=[Market.US]
        )

        mock_logger.warning.assert_not_called()
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.AUDI,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_tesla_data_quality_check_calls_the_logger_when_zero_model_loaded(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = []
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.TESLA, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with("[US-tesla] Zero Models Found")
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.TESLA,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_tesla_data_quality_check_calls_the_logger_when_option_included_has_non_zero_price(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.TESLA,
                market=Market.US,
                line_option_codes=[
                    create_test_line_item_option_code(
                        gross_list_price=100, included=True
                    ),
                    create_test_line_item_option_code(included=True),
                ],
                model_description="model",
                model_range_description="model range",
                line_description="line",
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.TESLA, markets=[Market.US]
        )

        mock_logger.warning.assert_called_with(
            "[US-tesla] Option Included has Non-Zero Price for model_range:model range model_description:model line_description:line"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.TESLA,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_audi_de_check_for_net_and_gross_negative_price_doesnt_log(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.AUDI,
                market=Market.DE,
                line_option_codes=[
                    create_test_line_item_option_code(
                        gross_list_price=0, included=True
                    ),
                    create_test_line_item_option_code(
                        gross_list_price=-110, included=False
                    ),
                ],
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.AUDI, markets=[Market.DE]
        )

        mock_logger.warning.assert_not_called()
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_audi_de_check_for_option_included_non_zero_price_logs_error(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.AUDI,
                market=Market.DE,
                line_option_codes=[
                    create_test_line_item_option_code(
                        gross_list_price=100, included=True
                    ),
                    create_test_line_item_option_code(
                        gross_list_price=110, included=False
                    ),
                ],
                model_description="model",
                model_range_description="model range",
                line_description="line",
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.AUDI, markets=[Market.DE]
        )

        mock_logger.warning.assert_called_with(
            "[DE-audi] Option Included has Non-Zero Price for model_range:model range model_description:model line_description:line"
        )
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
        )

    @patch.object(DataQualityCheck, "_check_for_included_options_with_non_zero_price")
    def test_bmw_de_shoud_not_call__check_for_included_options_with_non_zero_price(
        self, mock__check_for_included_options_with_non_zero_price
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.BMW,
                market=Market.DE,
                line_option_codes=[
                    create_test_line_item_option_code(
                        gross_list_price=100, included=True
                    ),
                    create_test_line_item_option_code(
                        gross_list_price=110, included=False
                    ),
                ],
            )
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.BMW, markets=[Market.DE]
        )

        assert mock__check_for_included_options_with_non_zero_price.call_count == 0
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.BMW,
        )

    @patch.object(DataQualityCheck, "_check_for_negative_price_for_options")
    def test_bmw_us_should_not_trigger_check_for_negative_price_for_options(
        self, mock__check_for_negative_price_for_options
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.BMW,
                market=Market.US,
                line_option_codes=[
                    create_test_line_item_option_code(
                        gross_list_price=-100, included=True
                    ),
                    create_test_line_item_option_code(
                        gross_list_price=-110, included=False
                    ),
                ],
            )
        ]
        assert mock__check_for_negative_price_for_options.call_count == 0
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.BMW, markets=[Market.US]
        )

        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.US,
            vendor=Vendor.BMW,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_check_for_check_for_model_duplication(self, mock_logger):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.AUDI,
                market=Market.DE,
                line_option_codes=[
                    create_test_line_item_option_code(
                        gross_list_price=0, included=True
                    ),
                    create_test_line_item_option_code(
                        gross_list_price=110, included=False
                    ),
                ],
                series="series",
                model_range_code="model range code",
                model_range_description="model range",
                model_code="model code",
                model_description="model",
                line_code="line code",
                line_description="line",
            ),
            create_test_line_item(
                vendor=Vendor.AUDI,
                market=Market.DE,
                line_option_codes=[
                    create_test_line_item_option_code(
                        gross_list_price=0, included=True
                    ),
                    create_test_line_item_option_code(
                        gross_list_price=110, included=False
                    ),
                ],
                series="series",
                model_range_code="model range code",
                model_range_description="model range",
                model_code="model code",
                model_description="model",
                line_code="line code",
                line_description="line",
            ),
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.AUDI, markets=[Market.DE]
        )

        mock_logger.warning.assert_called_with("[DE-audi] Duplication of Models Found")
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
        )

    @patch("src.price_monitor.data_quality.data_quality_checks.logger")
    def test_check_for_check_for_model_duplication_does_not_call_logger_when_there_is_no_duplication(
        self, mock_logger
    ):
        mock_repository = Mock()
        data_quality_checks = DataQualityCheck(mock_repository)
        mock_repository.load_market.return_value = [
            create_test_line_item(
                vendor=Vendor.AUDI,
                market=Market.DE,
                line_option_codes=[
                    create_test_line_item_option_code(
                        gross_list_price=0, included=True
                    ),
                    create_test_line_item_option_code(
                        gross_list_price=110, included=False
                    ),
                ],
                series="series",
                model_range_code="model range code",
                model_range_description="model range",
                model_code="model code",
                model_description="model",
                line_code="line code",
                line_description="line",
            ),
            create_test_line_item(
                vendor=Vendor.AUDI,
                market=Market.DE,
                line_option_codes=[
                    create_test_line_item_option_code(
                        gross_list_price=0, included=True
                    ),
                    create_test_line_item_option_code(
                        gross_list_price=110, included=False
                    ),
                ],
                series="series",
                model_range_code="model range code",
                model_range_description="model range",
                model_code="model code",
                model_description="model",
                line_code="line code1",
                line_description="line1",
            ),
        ]
        data_quality_checks.run_check_for_vendor_and_market(
            vendor=Vendor.AUDI, markets=[Market.DE]
        )

        mock_logger.warning.assert_not_called()
        mock_repository.load_market.assert_called_with(
            date=today_dashed_str_with_key(),
            market=Market.DE,
            vendor=Vendor.AUDI,
        )
