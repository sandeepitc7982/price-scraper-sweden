import unittest
from test.price_monitor.utils.test_data_builder import (
    create_difference_line_item,
    create_test_difference_item,
    create_test_line_item,
)
from unittest.mock import Mock, call, patch

from src.price_monitor.model.difference_item import DifferenceItem
from src.price_monitor.model.option_price_difference_item import (
    OptionPriceDifferenceItem,
)
from src.price_monitor.model.price_difference_item import PriceDifferenceItem
from src.price_monitor.price_comparer.comparator import Comparator
from src.price_monitor.utils.clock import (
    today_dashed_str_with_key,
    yesterday_dashed_str_with_key,
)

yesterday = yesterday_dashed_str_with_key()
today = today_dashed_str_with_key()


class TestComparator(unittest.TestCase):
    def init_comparator(self):
        return Comparator(
            {
                "output": {
                    "directory": "data",
                    "prices_filename": "",
                    "differences_filename": "",
                }
            }
        )

    @patch(
        "src.price_monitor.price_comparer.comparator.check_item_differences",
        return_value=create_difference_line_item(),
    )
    def test_load_differences_calls_loads_line_items_from_yesterday_and_today(
        self, mock_check_item_differences
    ):
        comparator = self.init_comparator()
        line_item_repository_mock = Mock()
        line_item_repository_mock.load.return_value = [create_test_line_item()]
        setattr(comparator, "line_item_repository", line_item_repository_mock)

        comparator._load_differences()

        line_item_repository_mock.load.assert_has_calls(
            [
                call(date=yesterday_dashed_str_with_key()),
                call(date=today_dashed_str_with_key()),
            ]
        )

    @patch(
        "src.price_monitor.price_comparer.comparator.Comparator._load_differences",
        return_value=(create_difference_line_item(), None),
    )
    def test_compare_loads_differences_and_saves_them_into_a_file(
        self, mock_load_diffs
    ):
        comparator = self.init_comparator()
        mock_diffs_repository = Mock()
        difference_item = create_test_difference_item()

        mock_load_diffs.return_value = ([difference_item], [], [])

        setattr(comparator, "differences_repository", mock_diffs_repository)

        comparator.compare()

        mock_diffs_repository.save.assert_has_calls(
            [
                call([create_test_difference_item()], DifferenceItem),
                call([], PriceDifferenceItem),
                call([], OptionPriceDifferenceItem),
            ]
        )

    @patch(
        "src.price_monitor.price_comparer.comparator.Comparator._load_differences",
        return_value=(None, create_test_difference_item()),
    )
    def test_compare_loads_price_differences_and_saves_them_into_a_file(
        self, mock_load_diffs
    ):
        comparator = self.init_comparator()
        mock_diffs_repository = Mock()
        setattr(comparator, "differences_repository", mock_diffs_repository)
        mock_load_diffs.return_value = ([create_test_difference_item()], [], [])

        comparator.compare()

        mock_diffs_repository.save.assert_has_calls(
            [
                call([create_test_difference_item()], DifferenceItem),
                call([], PriceDifferenceItem),
                call([], OptionPriceDifferenceItem),
            ]
        )

    @patch(
        "src.price_monitor.price_comparer.comparator.Comparator._load_differences",
        return_value=(None, create_test_difference_item()),
    )
    def test_compare_loads_option_price_differences_and_saves_them_into_a_file(
        self, mock_load_diffs
    ):
        comparator = self.init_comparator()
        mock_diffs_repository = Mock()
        setattr(comparator, "differences_repository", mock_diffs_repository)
        mock_load_diffs.return_value = ([create_test_difference_item()], [], [])

        comparator.compare()

        mock_diffs_repository.save.assert_has_calls(
            [
                call([create_test_difference_item()], DifferenceItem),
                call([], PriceDifferenceItem),
                call([], OptionPriceDifferenceItem),
            ]
        )
