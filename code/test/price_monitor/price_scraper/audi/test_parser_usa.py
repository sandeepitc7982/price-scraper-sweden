from pathlib import Path

from src.price_monitor.model.vendor import Vendor
from src.price_monitor.price_scraper.audi.parser_usa import (
    parse_available_model_range_links,
)

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"
VENDOR = Vendor.AUDI


def test_parse_available_model_range_links_when_price_is_present_it_should_return_in_first_list():
    expected_links_having_price = [
        "/us/web/en/models/e-tron-gt/e-tron-gt/2024/overview",
        "/us/web/en/models/e-tron-gt/rs-e-tron-gt/2024/overview",
        "/us/web/en/models/q4/q4-e-tron/2024/overview",
        "/us/web/en/models/q4/q4-sportback-e-tron/2024/overview",
        "/us/web/en/models/q8-e-tron/q8-e-tron/2024/overview",
        "/us/web/en/models/q8-e-tron/q8-sportback-e-tron/2024/overview",
        "/us/web/en/models/q8-e-tron/sq8-e-tron/2024/overview",
        "/us/web/en/models/q8-e-tron/sq8-sportback-e-tron/2024/overview",
        "/us/web/en/models/q3/q3/2024/overview",
        "/us/web/en/models/q5/q5/2023/overview",
        "/us/web/en/models/q5/q5-sportback/2024/overview",
        "/us/web/en/models/q5/sq5/2024/overview",
        "/us/web/en/models/q5/sq5-sportback/2024/overview",
        "/us/web/en/models/q7/q7/2024/overview",
        "/us/web/en/models/q7/sq7/2024/overview",
        "/us/web/en/models/q8/q8/2023/overview",
        "/us/web/en/models/q8/sq8/2023/overview",
        "/us/web/en/models/q8/rsq8/2024/overview",
        "/us/web/en/models/a3/a3/2024/overview",
        "/us/web/en/models/a3/s3/2024/overview",
        "/us/web/en/models/a3/rs3-sedan/2024/overview",
        "/us/web/en/models/a4/a4-sedan/2024/overview",
        "/us/web/en/models/a4/a4-allroad/2024/overview",
        "/us/web/en/models/a4/s4-sedan/2024/overview",
        "/us/web/en/models/a5/a5-coupe/2024/overview",
        "/us/web/en/models/a5/s5-coupe/2024/overview",
        "/us/web/en/models/a5/rs5-coupe/2024/overview",
        "/us/web/en/models/a5/a5-sportback/2024/overview",
        "/us/web/en/models/a5/s5-sportback/2024/overview",
        "/us/web/en/models/a5/rs5-sportback/2024/overview",
        "/us/web/en/models/a5/a5-cabriolet/2024/overview",
        "/us/web/en/models/a5/s5-cabriolet/2024/overview",
        "/us/web/en/models/a6/a6-sedan/2024/overview",
        "/us/web/en/models/a6/s6-sedan/2024/overview",
        "/us/web/en/models/a6/a6-allroad/2024/overview",
        "/us/web/en/models/a6/rs6-avant/2024/overview",
        "/us/web/en/models/a7/a7-sportback/2024/overview",
        "/us/web/en/models/a7/s7-sportback/2024/overview",
        "/us/web/en/models/a7/rs7/2024/overview",
        "/us/web/en/models/a8/a8-sedan/2024/overview",
        "/us/web/en/models/a8/s8-sedan/2024/overview",
    ]

    with open(f"{TEST_DATA_DIR}/model_list_us.html", "r") as file:
        links_having_price, links_not_having_price = parse_available_model_range_links(
            file.read()
        )
        assert expected_links_having_price == links_having_price


def test_parse_available_model_range_links_when_price_is_not_present_it_should_return_in_second_list():
    expected_links_not_having_price = [
        "/us/web/en/models/tt/tt-heritage/2024/overview",
        "/us/web/en/models/r8/r8-heritage/2024/overview",
    ]

    with open(f"{TEST_DATA_DIR}/model_list_us.html", "r") as file:
        links_having_price, links_not_having_price = parse_available_model_range_links(
            file.read()
        )
        assert expected_links_not_having_price == links_not_having_price
