import unittest

from src.price_monitor.finance_comparer.difference_finance_item import (
    build_difference_for_finance_item,
    FinanceItemDifferenceReason,
)
from src.price_monitor.finance_comparer.finance_line_difference_checker import (
    check_item_differences,
)
from src.price_monitor.utils.clock import today_dashed_str, yesterday_dashed_str
from test.price_monitor.utils.test_data_builder import (
    create_test_finance_line_item,
    create_difference_finance_line_item,
)


class TestFinanceLineDiffChecker(unittest.TestCase):
    def test_detects_new_finance_line(self):

        new_line = create_test_finance_line_item(
            date=today_dashed_str(), series="C", contract_type="PCP"
        )

        prev_dataset = [
            create_test_finance_line_item(
                date=yesterday_dashed_str(), series="A", contract_type="PCP"
            ),
            create_test_finance_line_item(
                date=yesterday_dashed_str(), series="B", contract_type="PCP"
            ),
        ]
        current_dataset = [
            create_test_finance_line_item(
                date=today_dashed_str(), series="A", contract_type="PCP"
            ),
            create_test_finance_line_item(
                date=today_dashed_str(), series="B", contract_type="PCP"
            ),
            new_line,
        ]

        actual = check_item_differences(current=current_dataset, previous=prev_dataset)

        assert actual == [
            build_difference_for_finance_item(
                finance_line_item=new_line,
                reason=FinanceItemDifferenceReason.PCP_NEW_LINE,
            )
        ]

    def test_detects_removed_line(self):
        removed_line = create_test_finance_line_item(
            date=today_dashed_str(), series="C", contract_type="PCP"
        )

        prev_dataset = [
            create_test_finance_line_item(
                date=today_dashed_str(), series="A", contract_type="PCP"
            ),
            removed_line,
        ]

        current_dataset = [
            create_test_finance_line_item(
                date=today_dashed_str(), series="A", contract_type="PCP"
            )
        ]

        assert check_item_differences(
            current=current_dataset, previous=prev_dataset
        ) == [
            build_difference_for_finance_item(
                finance_line_item=removed_line,
                reason=FinanceItemDifferenceReason.PCP_LINE_REMOVED,
            )
        ]

    def test_detects_monthly_rental_glp_change(self):
        current_dataset = [
            create_test_finance_line_item(
                date=today_dashed_str(),
                series="C",
                contract_type="PCP",
                monthly_rental_glp=567,
            )
        ]

        prev_dataset = [
            create_test_finance_line_item(
                date=yesterday_dashed_str(),
                series="C",
                contract_type="PCP",
                monthly_rental_glp=496,
            )
        ]

        expected_difference = create_difference_finance_line_item(
            vehicle_id="de_aud_8939f3ac",
            vendor="audi",
            series="C",
            model_range_code="test",
            model_range_description="test",
            model_code="test",
            model_description="test",
            line_code="test",
            line_description="test",
            old_value=496,
            new_value=567,
            reason=FinanceItemDifferenceReason.PCP_MONTHLY_RENTAL_CHANGED,
            market="DE",
        )

        assert check_item_differences(
            current=current_dataset, previous=prev_dataset
        ) == [expected_difference]

    def test_detects_otr_change(self):
        current_dataset = [
            create_test_finance_line_item(
                date=today_dashed_str(),
                series="C",
                contract_type="PCP",
                otr=65000,
            )
        ]

        prev_dataset = [
            create_test_finance_line_item(
                date=yesterday_dashed_str(),
                series="C",
                contract_type="PCP",
                otr=60000,
            )
        ]

        expected_difference = create_difference_finance_line_item(
            vehicle_id="de_aud_8939f3ac",
            vendor="audi",
            series="C",
            model_range_code="test",
            model_range_description="test",
            model_code="test",
            model_description="test",
            line_code="test",
            line_description="test",
            old_value=60000,
            new_value=65000,
            reason=FinanceItemDifferenceReason.PCP_OTR_CHANGED,
            market="DE",
        )

        assert check_item_differences(
            current=current_dataset, previous=prev_dataset
        ) == [expected_difference]

    def test_detects_apr_change(self):
        current_dataset = [
            create_test_finance_line_item(
                date=today_dashed_str(),
                series="C",
                contract_type="PCP",
                apr=9.9,
            )
        ]

        prev_dataset = [
            create_test_finance_line_item(
                date=yesterday_dashed_str(),
                series="C",
                contract_type="PCP",
                apr=9.0,
            )
        ]

        expected_difference = create_difference_finance_line_item(
            vehicle_id="de_aud_8939f3ac",
            vendor="audi",
            series="C",
            model_range_code="test",
            model_range_description="test",
            model_code="test",
            model_description="test",
            line_code="test",
            line_description="test",
            old_value=9.0,
            new_value=9.9,
            reason=FinanceItemDifferenceReason.PCP_APR_CHANGED,
            market="DE",
        )

        assert check_item_differences(
            current=current_dataset, previous=prev_dataset
        ) == [expected_difference]

    def test_detects_sales_offer_change(self):
        current_dataset = [
            create_test_finance_line_item(
                date=today_dashed_str(),
                series="C",
                contract_type="PCP",
                sales_offer=567,
            )
        ]

        prev_dataset = [
            create_test_finance_line_item(
                date=yesterday_dashed_str(),
                series="C",
                contract_type="PCP",
                sales_offer=496,
            )
        ]

        expected_difference = create_difference_finance_line_item(
            vehicle_id="de_aud_8939f3ac",
            vendor="audi",
            series="C",
            model_range_code="test",
            model_range_description="test",
            model_code="test",
            model_description="test",
            line_code="test",
            line_description="test",
            old_value=496,
            new_value=567,
            reason=FinanceItemDifferenceReason.PCP_SALES_OFFER_CHANGED,
            market="DE",
        )

        assert check_item_differences(
            current=current_dataset, previous=prev_dataset
        ) == [expected_difference]

    def test_detects_fixed_roi_change(self):
        current_dataset = [
            create_test_finance_line_item(
                date=today_dashed_str(),
                series="C",
                contract_type="PCP",
                fixed_roi=6.7,
            )
        ]

        prev_dataset = [
            create_test_finance_line_item(
                date=yesterday_dashed_str(),
                series="C",
                contract_type="PCP",
                fixed_roi=7.3,
            )
        ]

        expected_difference = create_difference_finance_line_item(
            vehicle_id="de_aud_8939f3ac",
            vendor="audi",
            series="C",
            model_range_code="test",
            model_range_description="test",
            model_code="test",
            model_description="test",
            line_code="test",
            line_description="test",
            old_value=7.3,
            new_value=6.7,
            reason=FinanceItemDifferenceReason.PCP_FIXED_ROI_CHANGED,
            market="DE",
        )

        assert check_item_differences(
            current=current_dataset, previous=prev_dataset
        ) == [expected_difference]

    def test_detects_optional_final_payment_change(self):
        current_dataset = [
            create_test_finance_line_item(
                date=today_dashed_str(),
                series="C",
                contract_type="PCP",
                optional_final_payment=567,
            )
        ]

        prev_dataset = [
            create_test_finance_line_item(
                date=yesterday_dashed_str(),
                series="C",
                contract_type="PCP",
                optional_final_payment=496,
            )
        ]

        expected_difference = create_difference_finance_line_item(
            vehicle_id="de_aud_8939f3ac",
            vendor="audi",
            series="C",
            model_range_code="test",
            model_range_description="test",
            model_code="test",
            model_description="test",
            line_code="test",
            line_description="test",
            old_value=496,
            new_value=567,
            reason=FinanceItemDifferenceReason.PCP_OPTIONAL_FINAL_PAYMENT_CHANGED,
            market="DE",
        )

        assert check_item_differences(
            current=current_dataset, previous=prev_dataset
        ) == [expected_difference]
