import unittest
from unittest.mock import patch, Mock, call

from src.price_monitor.finance_comparer.difference_finance_item import (
    DifferenceFinanceItem,
)
from src.price_monitor.finance_comparer.finance_options_comparator import (
    FinanceOptionsComparator,
)
from src.price_monitor.utils.clock import (
    yesterday_dashed_str_with_key,
    today_dashed_str_with_key,
)
from test.price_monitor.utils.test_data_builder import (
    create_difference_finance_line_item,
    create_test_finance_line_item,
)


class TestFinanceComparator(unittest.TestCase):
    def init_comparator(self):
        return FinanceOptionsComparator(
            {
                "output": {
                    "directory": "data",
                    "prices_filename": "",
                    "differences_filename": "",
                    "finance_options_filename": "finance_options",
                }
            }
        )

    @patch(
        "src.price_monitor.finance_comparer.finance_line_difference_checker.check_item_differences",
        return_value=create_difference_finance_line_item(),
    )
    def test_load_differences_calls_loads_finance_line_items_from_yesterday_and_today(
        self, mock_check_item_differences
    ):
        comparator = self.init_comparator()
        finance_item_repository_mock = Mock()
        finance_item_repository_mock.load.return_value = [
            create_test_finance_line_item()
        ]
        setattr(comparator, "finance_item_repository", finance_item_repository_mock)

        comparator._load_differences()

        finance_item_repository_mock.load.assert_has_calls(
            [
                call(date=yesterday_dashed_str_with_key()),
                call(date=today_dashed_str_with_key()),
            ]
        )

    @patch(
        "src.price_monitor.finance_comparer.finance_options_comparator.FinanceOptionsComparator._load_differences",
        return_value=[create_difference_finance_line_item()],
    )
    def test_compare_loads_finance_options_differences_and_saves_them_into_a_file(
        self, mock_load_diffs
    ):
        comparator = self.init_comparator()
        mock_diffs_repository = Mock()

        setattr(
            comparator, "differences_finance_item_repository", mock_diffs_repository
        )

        comparator.compare()

        mock_diffs_repository.save.assert_has_calls(
            [
                call([create_difference_finance_line_item()], DifferenceFinanceItem),
            ]
        )
