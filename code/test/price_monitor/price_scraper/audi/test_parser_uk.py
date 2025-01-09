from pathlib import Path

from src.price_monitor.model.vendor import Vendor
from src.price_monitor.price_scraper.audi.parser_uk import (
    parse_available_model_range_links,
)

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"
VENDOR = Vendor.AUDI


def test_parse_available_model_range_links():
    expected_links_having_price = [
        "etrongt/audi-e-tron-gt",
        "etrongt/audi-rs-e-tron-gt",
        "a1/a1-sportback",
        "a3/a3-sportback",
        "a3/a3-tfsi-e",
        "a3/a3-saloon",
        "a3/s3-saloon",
        "a3/s3-sportback",
        "a3/rs-3-sportback",
        "a3/rs-3-saloon",
        "a4/a4-saloon",
        "a4/a4-avant",
        "a4/rs-4-avant",
        "a5/a5-coupe",
        "a5/a5-sportback",
        "a5/rs-5-coupe",
        "a5/rs-5-sportback",
        "a6/a6-saloon",
        "a6/a6-tfsi-e",
        "a6/a6-avant",
        "a6/a6-avant-tfsi-e",
        "a6/s6-saloon",
        "a6/s6-avant",
        "a6/rs-6-avant",
        "a7/a7-sportback",
        "a7/a7-tfsi-e",
        "a7/s7-sportback",
        "a7/rs-7-sportback",
        "a8/a8",
        "a8/a8-tfsi-e",
        "a8/a8-l",
        "a8/a8-l-tfsi-e",
        "a8/s8",
        "q2/q2",
        "q2/sq2",
        "q3/q3",
        "q3/q3-tfsi-e",
        "q3/q3-sportback",
        "q3/q3-sportback-tfsi-e",
        "q4/q4-e-tron",
        "q4/q4-e-tron-sportback",
        "q5/q5",
        "q5/q5-tfsi-e",
        "q5/q5-sportback",
        "q5/q5-sportback-tfsi-e",
        "q7/q7",
        "q7/sq7",
        "q8/q8",
        "q8/sq8",
        "q8/rsq8",
        "q8-e-tron/q8-e-tron",
        "q8-e-tron/q8-sportback-e-tron",
        "q8-e-tron/sq8-e-tron",
        "q8-e-tron/sq8-sportback-e-tron",
        "r8/r8-coupe",
        "tt/tt-coupe",
        "tt/tts-coupe",
    ]
    with open(f"{TEST_DATA_DIR}/uk_model_list.html", "r") as file:
        model_links = parse_available_model_range_links(file.read())
        assert expected_links_having_price == model_links
