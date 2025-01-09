import json
from pathlib import Path
from test.price_monitor.utils.test_data_builder import create_test_line_item

from src.price_monitor.model.line_item_option_code import LineItemOptionCode
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import LineItem
from src.price_monitor.price_scraper.tesla.parser import (
    adjust_otr_price,
    get_line_description,
    parse_available_models_links,
    parse_line_items,
    parse_model_and_series,
    parse_otr_price,
)
from src.price_monitor.utils.clock import today_dashed_str

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"
VENDOR = Vendor.TESLA


def test_parse_line_items_for_models():
    expected_models_line_items = [
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="ms",
            model_range_code="$MDLS",
            model_range_description="Model S",
            model_code="$MTS13",
            model_description="Model S",
            line_code="$MTS13",
            line_description="Maximale Reichweite",
            line_option_codes=[
                LineItemOptionCode(
                    **{
                        "code": "$WS10",
                        "description": "21-Zoll Arachnid-Felgen",
                        "type": "WHEELS",
                        "included": False,
                        "net_list_price": 4117.65,
                        "gross_list_price": 4900,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ICW00",
                        "description": "Premium-Innenraum Creme mit Walnuss Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": False,
                        "net_list_price": 2016.81,
                        "gross_list_price": 2400,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ST0Y",
                        "description": "Yoke-Lenkung",
                        "type": "STEERING_WHEEL",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APF2",
                        "description": "Volles Potenzial f\u00fcr autonomes Fahren",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 6302.52,
                        "gross_list_price": 7500,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSB",
                        "description": "Deep Blue Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1848.74,
                        "gross_list_price": 2200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSW",
                        "description": "Pearl White Multi-Coat",
                        "type": "PAINT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ST03",
                        "description": "Lenkrad",
                        "type": "STEERING_WHEEL",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$WS90",
                        "description": "19-Zoll Tempest-Felgen",
                        "type": "WHEELS",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PMNG",
                        "description": "Midnight Silver Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1848.74,
                        "gross_list_price": 2200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IBE00",
                        "description": "Komplett schwarz Premium-Innenraum mit Ebenholz Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$SC04",
                        "description": "Supercharger-Abrechnung pro Nutzung",
                        "type": "SUPER_CHARGER",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PR01",
                        "description": "Ultra Red",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 2689.08,
                        "gross_list_price": 3200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IWW00",
                        "description": "Premium-Innenraum schwarz und wei\u00df mit Walnuss Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": False,
                        "net_list_price": 2016.81,
                        "gross_list_price": 2400,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APPB",
                        "description": "Enhanced Autopilot",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 3193.28,
                        "gross_list_price": 3800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APBS",
                        "description": "Autopilot",
                        "type": "AUTOPILOT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PBSB",
                        "description": "Solid Black",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1512.61,
                        "gross_list_price": 1800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CPF0",
                        "description": "Standard-Konnektivit\u00e4t",
                        "type": "CONNECTIVITY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
            ],
            currency="EUR",
            net_list_price=94949.58,
            gross_list_price=112990,
            market=Market.DE,
        ),
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="ms",
            model_range_code="$MDLS",
            model_range_description="Model S",
            model_code="$MTS14",
            model_description="Model S",
            line_code="$MTS14",
            line_description="Plaid",
            line_option_codes=[
                LineItemOptionCode(
                    **{
                        "code": "$ST0Y",
                        "description": "Yoke-Lenkung",
                        "type": "STEERING_WHEEL",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IBC00",
                        "description": "Komplett schwarz Premium-Innenraum mit Karbonfaser Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APF2",
                        "description": "Volles Potenzial f\u00fcr autonomes Fahren",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 6302.52,
                        "gross_list_price": 7500,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSB",
                        "description": "Deep Blue Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1848.74,
                        "gross_list_price": 2200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSW",
                        "description": "Pearl White Multi-Coat",
                        "type": "PAINT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ST03",
                        "description": "Lenkrad",
                        "type": "STEERING_WHEEL",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PMNG",
                        "description": "Midnight Silver Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1848.74,
                        "gross_list_price": 2200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$SC04",
                        "description": "Supercharger-Abrechnung pro Nutzung",
                        "type": "SUPER_CHARGER",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PR01",
                        "description": "Ultra Red",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 2689.08,
                        "gross_list_price": 3200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IWC00",
                        "description": "Premium-Innenraum schwarz und wei\u00df mit Karbonfaser Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": False,
                        "net_list_price": 2016.81,
                        "gross_list_price": 2400,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APPB",
                        "description": "Enhanced Autopilot",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 3193.28,
                        "gross_list_price": 3800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APBS",
                        "description": "Autopilot",
                        "type": "AUTOPILOT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PBSB",
                        "description": "Solid Black",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1512.61,
                        "gross_list_price": 1800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$WS12",
                        "description": "21-Zoll Arachnid-Felgen",
                        "type": "WHEELS",
                        "included": False,
                        "net_list_price": 4117.65,
                        "gross_list_price": 4900,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ICC00",
                        "description": "Innenraum Creme mit Karbonfaser Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": False,
                        "net_list_price": 2016.81,
                        "gross_list_price": 2400,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CPF0",
                        "description": "Standard-Konnektivit\u00e4t",
                        "type": "CONNECTIVITY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
            ],
            currency="EUR",
            net_list_price=115957.98,
            gross_list_price=137990,
            market=Market.DE,
        ),
    ]

    with open(f"{TEST_DATA_DIR}/models_de.html", "r") as payload:
        for item in parse_line_items(payload.read(), Market.DE):
            assert item in expected_models_line_items
            expected_line_item = expected_models_line_items[
                expected_models_line_items.index(item)
            ]
            item.line_option_codes.sort(key=lambda x: x.code)
            expected_line_item.line_option_codes.sort(key=lambda x: x.code)
            assert item == expected_line_item


def test_parse_line_items_for_modelx():
    expected_models_line_items = [
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="mx",
            model_range_code="$MDLX",
            model_range_description="Model X",
            model_code="$MTX14",
            model_description="Model X",
            line_code="$MTX14",
            line_description="Plaid",
            line_option_codes=[
                LineItemOptionCode(
                    **{
                        "code": "$ST0Y",
                        "description": "Yoke-Lenkung",
                        "type": "STEERING_WHEEL",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IBC00",
                        "description": "Komplett schwarz Premium-Innenraum mit Karbonfaser Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APF2",
                        "description": "Volles Potenzial f\u00fcr autonomes Fahren",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 6302.52,
                        "gross_list_price": 7500,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSB",
                        "description": "Deep Blue Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1848.74,
                        "gross_list_price": 2200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSW",
                        "description": "Pearl White Multi-Coat",
                        "type": "PAINT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ST03",
                        "description": "Lenkrad",
                        "type": "STEERING_WHEEL",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$WX21",
                        "description": "22-Zoll Turbine-Felgen",
                        "type": "WHEELS",
                        "included": False,
                        "net_list_price": 4957.98,
                        "gross_list_price": 5900,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CC02",
                        "description": "6-Sitzer",
                        "type": "REAR_SEATS",
                        "included": False,
                        "net_list_price": 6470.59,
                        "gross_list_price": 7700,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PMNG",
                        "description": "Midnight Silver Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1848.74,
                        "gross_list_price": 2200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$SC04",
                        "description": "Supercharger-Abrechnung pro Nutzung",
                        "type": "SUPER_CHARGER",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PR01",
                        "description": "Ultra Red",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 2689.08,
                        "gross_list_price": 3200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IWC00",
                        "description": "Premium-Innenraum schwarz und wei\u00df mit Karbonfaser Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": False,
                        "net_list_price": 2016.81,
                        "gross_list_price": 2400,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APPB",
                        "description": "Enhanced Autopilot",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 3193.28,
                        "gross_list_price": 3800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APBS",
                        "description": "Autopilot",
                        "type": "AUTOPILOT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PBSB",
                        "description": "Solid Black",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1512.61,
                        "gross_list_price": 1800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ICC00",
                        "description": "Innenraum Creme mit Karbonfaser Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": False,
                        "net_list_price": 2016.81,
                        "gross_list_price": 2400,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CPF0",
                        "description": "Standard-Konnektivit\u00e4t",
                        "type": "CONNECTIVITY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
            ],
            currency="EUR",
            gross_list_price=140990,
            net_list_price=118478.99,
            market=Market.DE,
        ),
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="mx",
            model_range_code="$MDLX",
            model_range_description="Model X",
            model_code="$MTX13",
            model_description="Model X",
            line_code="$MTX13",
            line_description="Maximale Reichweite",
            line_option_codes=[
                LineItemOptionCode(
                    **{
                        "code": "$ICW00",
                        "description": "Premium-Innenraum Creme mit Walnuss Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": False,
                        "net_list_price": 2016.81,
                        "gross_list_price": 2400,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ST0Y",
                        "description": "Yoke-Lenkung",
                        "type": "STEERING_WHEEL",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APF2",
                        "description": "Volles Potenzial f\u00fcr autonomes Fahren",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 6302.52,
                        "gross_list_price": 7500,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSB",
                        "description": "Deep Blue Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1848.74,
                        "gross_list_price": 2200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSW",
                        "description": "Pearl White Multi-Coat",
                        "type": "PAINT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ST03",
                        "description": "Lenkrad",
                        "type": "STEERING_WHEEL",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CC02",
                        "description": "6-Sitzer",
                        "type": "REAR_SEATS",
                        "included": False,
                        "net_list_price": 6470.59,
                        "gross_list_price": 7700,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PMNG",
                        "description": "Midnight Silver Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1848.74,
                        "gross_list_price": 2200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CC01",
                        "description": "5-Sitzer",
                        "type": "REAR_SEATS",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IBE00",
                        "description": "Komplett schwarz Premium-Innenraum mit Ebenholz Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CC04",
                        "description": "7-Sitzer",
                        "type": "REAR_SEATS",
                        "included": False,
                        "net_list_price": 3529.41,
                        "gross_list_price": 4200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$WX20",
                        "description": "22-Zoll Turbine-Felgen",
                        "type": "WHEELS",
                        "included": False,
                        "net_list_price": 4957.98,
                        "gross_list_price": 5900,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$WX00",
                        "description": "20-Zoll Cyberstream-Felgen",
                        "type": "WHEELS",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$SC04",
                        "description": "Supercharger-Abrechnung pro Nutzung",
                        "type": "SUPER_CHARGER",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PR01",
                        "description": "Ultra Red",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 2689.08,
                        "gross_list_price": 3200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IWW00",
                        "description": "Premium-Innenraum schwarz und wei\u00df mit Walnuss Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": False,
                        "net_list_price": 2016.81,
                        "gross_list_price": 2400,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APPB",
                        "description": "Enhanced Autopilot",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 3193.28,
                        "gross_list_price": 3800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APBS",
                        "description": "Autopilot",
                        "type": "AUTOPILOT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PBSB",
                        "description": "Solid Black",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1512.61,
                        "gross_list_price": 1800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CPF0",
                        "description": "Standard-Konnektivit\u00e4t",
                        "type": "CONNECTIVITY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
            ],
            currency="EUR",
            net_list_price=101672.27,
            gross_list_price=120990,
            market=Market.DE,
        ),
    ]

    with open(f"{TEST_DATA_DIR}/modelx_de.html", "r") as payload:
        for item in parse_line_items(payload.read(), Market.DE):
            assert item in expected_models_line_items
            expected_line_item = expected_models_line_items[
                expected_models_line_items.index(item)
            ]
            item.line_option_codes.sort(key=lambda x: x.code)
            expected_line_item.line_option_codes.sort(key=lambda x: x.code)
            assert item == expected_line_item


def test_parse_line_items_for_model3():
    expected_models_line_items = [
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="m3",
            model_range_code="$MDL3",
            model_range_description="Model 3 2023 Europa",
            model_code="$MT328",
            model_description="Model 3 2023 Europa",
            line_code="$MT328",
            line_description="Maximale Reichweite mit AWD",
            line_option_codes=[
                LineItemOptionCode(
                    **{
                        "code": "$PRM31",
                        "description": "Premium-Innenraum",
                        "type": "PREMIUM_PACKAGE",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APF2",
                        "description": "Volles Potenzial f\u00fcr autonomes Fahren",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 6302.52,
                        "gross_list_price": 7500,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$W3WE9",
                        "description": '19" Pirelli-Winterreifensatz',
                        "type": "WINTER_WHEELS",
                        "included": False,
                        "net_list_price": 2512.61,
                        "gross_list_price": 2990,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSB",
                        "description": "Deep Blue Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1344.54,
                        "gross_list_price": 1600,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IPW1",
                        "description": "Premium-Innenraum schwarz und wei\u00df",
                        "type": "INTERIOR",
                        "included": False,
                        "net_list_price": 1008.4,
                        "gross_list_price": 1200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSW",
                        "description": "Pearl White Multi-Coat",
                        "type": "PAINT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$W3WE8",
                        "description": '18" Pirelli-Winterreifensatz',
                        "type": "WINTER_WHEELS",
                        "included": False,
                        "net_list_price": 1722.69,
                        "gross_list_price": 2050,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$TW01",
                        "description": "Anh\u00e4ngerkupplung",
                        "type": "TOWING",
                        "included": False,
                        "net_list_price": 1134.45,
                        "gross_list_price": 1350,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$W40B",
                        "description": "18-Zoll Aero-Felgen",
                        "type": "WHEELS",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPMR",
                        "description": "Red Multi-Coat",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1680.67,
                        "gross_list_price": 2000,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IPB1",
                        "description": "Premium-Innenraum komplett schwarz",
                        "type": "INTERIOR",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PMNG",
                        "description": "Midnight Silver Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1344.54,
                        "gross_list_price": 1600,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$SC04",
                        "description": "Supercharger-Zugang + Pay-As-You-Go",
                        "type": "SUPER_CHARGER",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APPB",
                        "description": "Enhanced Autopilot",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 3193.28,
                        "gross_list_price": 3800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APBS",
                        "description": "Autopilot",
                        "type": "AUTOPILOT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PBSB",
                        "description": "Solid Black",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1008.4,
                        "gross_list_price": 1200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CPF0",
                        "description": "Standard-Konnektivit\u00e4t",
                        "type": "CONNECTIVITY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$W41B",
                        "description": "19-Zoll Sport-Felgen",
                        "type": "WHEELS",
                        "included": False,
                        "net_list_price": 1428.57,
                        "gross_list_price": 1700,
                    }
                ),
            ],
            currency="EUR",
            net_list_price=45369.75,
            gross_list_price=53990,
            market=Market.DE,
        ),
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="m3",
            model_range_code="$MDL3",
            model_range_description="Model 3 2023 Europa",
            model_code="$MT325",
            model_description="Model 3 2023 Europa",
            line_code="$MT325",
            line_description="Performance",
            line_option_codes=[
                LineItemOptionCode(
                    **{
                        "code": "$PL31",
                        "description": "Performance-Pedale",
                        "type": "PEDALS",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PRM31",
                        "description": "Premium-Innenraum",
                        "type": "PREMIUM_PACKAGE",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APF2",
                        "description": "Volles Potenzial f\u00fcr autonomes Fahren",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 6302.52,
                        "gross_list_price": 7500,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSB",
                        "description": "Deep Blue Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1344.54,
                        "gross_list_price": 1600,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IPW1",
                        "description": "Premium-Innenraum schwarz und wei\u00df",
                        "type": "INTERIOR",
                        "included": False,
                        "net_list_price": 1008.4,
                        "gross_list_price": 1200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSW",
                        "description": "Pearl White Multi-Coat",
                        "type": "PAINT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$SLR1",
                        "description": "Karbonfaser-Spoiler",
                        "type": "SPOILER",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPMR",
                        "description": "Red Multi-Coat",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1680.67,
                        "gross_list_price": 2000,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$W33D",
                        "description": "20-Zoll \u00dcberturbine-Felgen",
                        "type": "WHEELS",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IPB1",
                        "description": "Premium-Innenraum komplett schwarz",
                        "type": "INTERIOR",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PMNG",
                        "description": "Midnight Silver Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1344.54,
                        "gross_list_price": 1600,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$SC04",
                        "description": "Supercharger-Zugang + Pay-As-You-Go",
                        "type": "SUPER_CHARGER",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$BC3R",
                        "description": "Performance-Bremsen",
                        "type": "BRAKES",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APPB",
                        "description": "Enhanced Autopilot",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 3193.28,
                        "gross_list_price": 3800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$WW300",
                        "description": '20" Pirelli-Winterreifensatz',
                        "type": "WINTER_WHEELS",
                        "included": False,
                        "net_list_price": 3361.34,
                        "gross_list_price": 4000,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APBS",
                        "description": "Autopilot",
                        "type": "AUTOPILOT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PBSB",
                        "description": "Solid Black",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1008.4,
                        "gross_list_price": 1200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$SPT31",
                        "description": "Zusatzausstattung \u201ePerformance\u201c",
                        "type": "SPORT_PACKAGE",
                        "included": False,
                        "net_list_price": 3462.18,
                        "gross_list_price": 4120,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CPF0",
                        "description": "Standard-Konnektivit\u00e4t",
                        "type": "CONNECTIVITY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
            ],
            currency="EUR",
            net_list_price=51252.10,
            gross_list_price=60990,
            market=Market.DE,
        ),
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="m3",
            model_range_code="$MDL3",
            model_range_description="Model 3 2023 Europa",
            model_code="$MT322",
            model_description="Model 3 2023 Europa",
            line_code="$MT322",
            line_description="Hinterradantrieb",
            line_option_codes=[
                LineItemOptionCode(
                    **{
                        "code": "$APF2",
                        "description": "Volles Potenzial f\u00fcr autonomes Fahren",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 6302.52,
                        "gross_list_price": 7500,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$W3WE9",
                        "description": '19" Pirelli-Winterreifensatz',
                        "type": "WINTER_WHEELS",
                        "included": False,
                        "net_list_price": 2512.61,
                        "gross_list_price": 2990,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSB",
                        "description": "Deep Blue Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1344.54,
                        "gross_list_price": 1600,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSW",
                        "description": "Pearl White Multi-Coat",
                        "type": "PAINT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$W3WE8",
                        "description": '18" Pirelli-Winterreifensatz',
                        "type": "WINTER_WHEELS",
                        "included": False,
                        "net_list_price": 1722.69,
                        "gross_list_price": 2050,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$TW01",
                        "description": "Anh\u00e4ngerkupplung",
                        "type": "TOWING",
                        "included": False,
                        "net_list_price": 1134.45,
                        "gross_list_price": 1350,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$W40B",
                        "description": "18-Zoll Aero-Felgen",
                        "type": "WHEELS",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPMR",
                        "description": "Red Multi-Coat",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1680.67,
                        "gross_list_price": 2000,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IBW1",
                        "description": "Innenraum schwarz und wei\u00df",
                        "type": "INTERIOR",
                        "included": False,
                        "net_list_price": 1008.4,
                        "gross_list_price": 1200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PMNG",
                        "description": "Midnight Silver Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1344.54,
                        "gross_list_price": 1600,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IBB1",
                        "description": "Innenraum komplett schwarz",
                        "type": "INTERIOR",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$SC04",
                        "description": "Supercharger-Zugang + Pay-As-You-Go",
                        "type": "SUPER_CHARGER",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PRM30",
                        "description": "Partieller Premium-Innenraum",
                        "type": "PREMIUM_PACKAGE",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APPB",
                        "description": "Enhanced Autopilot",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 3193.28,
                        "gross_list_price": 3800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APBS",
                        "description": "Autopilot",
                        "type": "AUTOPILOT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PBSB",
                        "description": "Solid Black",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1008.4,
                        "gross_list_price": 1200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CPF0",
                        "description": "Standard-Konnektivit\u00e4t",
                        "type": "CONNECTIVITY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$W41B",
                        "description": "19-Zoll Sport-Felgen",
                        "type": "WHEELS",
                        "included": False,
                        "net_list_price": 1428.57,
                        "gross_list_price": 1700,
                    }
                ),
            ],
            currency="EUR",
            net_list_price=36966.39,
            gross_list_price=43990,
            market=Market.DE,
        ),
    ]

    with open(f"{TEST_DATA_DIR}/model3_de.html", "r") as payload:
        for item in parse_line_items(payload.read(), Market.DE):
            assert item in expected_models_line_items
            expected_line_item = expected_models_line_items[
                expected_models_line_items.index(item)
            ]
            item.line_option_codes.sort(key=lambda x: x.code)
            expected_line_item.line_option_codes.sort(key=lambda x: x.code)
            assert item == expected_line_item


def test_parse_available_options_for_model():
    expected_models_line_items = [
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="mx",
            model_range_code="$MDLX",
            model_range_description="Model X",
            model_code="$MTX14",
            model_description="Model X",
            line_code="$MTX14",
            line_description="Plaid",
            line_option_codes=[
                LineItemOptionCode(
                    **{
                        "code": "$ST0Y",
                        "description": "Yoke-Lenkung",
                        "type": "STEERING_WHEEL",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IBC00",
                        "description": "Komplett schwarz Premium-Innenraum mit Karbonfaser Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APF2",
                        "description": "Volles Potenzial f\u00fcr autonomes Fahren",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 6302.52,
                        "gross_list_price": 7500,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSB",
                        "description": "Deep Blue Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1848.74,
                        "gross_list_price": 2200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSW",
                        "description": "Pearl White Multi-Coat",
                        "type": "PAINT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ST03",
                        "description": "Lenkrad",
                        "type": "STEERING_WHEEL",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$WX21",
                        "description": "22-Zoll Turbine-Felgen",
                        "type": "WHEELS",
                        "included": False,
                        "net_list_price": 4957.98,
                        "gross_list_price": 5900,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CC02",
                        "description": "6-Sitzer",
                        "type": "REAR_SEATS",
                        "included": False,
                        "net_list_price": 6470.59,
                        "gross_list_price": 7700,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PMNG",
                        "description": "Midnight Silver Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1848.74,
                        "gross_list_price": 2200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$SC04",
                        "description": "Supercharger-Abrechnung pro Nutzung",
                        "type": "SUPER_CHARGER",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PR01",
                        "description": "Ultra Red",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 2689.08,
                        "gross_list_price": 3200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IWC00",
                        "description": "Premium-Innenraum schwarz und wei\u00df mit Karbonfaser Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": False,
                        "net_list_price": 2016.81,
                        "gross_list_price": 2400,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APPB",
                        "description": "Enhanced Autopilot",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 3193.28,
                        "gross_list_price": 3800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APBS",
                        "description": "Autopilot",
                        "type": "AUTOPILOT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PBSB",
                        "description": "Solid Black",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1512.61,
                        "gross_list_price": 1800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ICC00",
                        "description": "Innenraum Creme mit Karbonfaser Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": False,
                        "net_list_price": 2016.81,
                        "gross_list_price": 2400,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CPF0",
                        "description": "Standard-Konnektivit\u00e4t",
                        "type": "CONNECTIVITY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
            ],
            currency="EUR",
            gross_list_price=140990,
            net_list_price=118478.99,
            market=Market.DE,
        ),
        LineItem(
            recorded_at=today_dashed_str(),
            last_scraped_on=today_dashed_str(),
            vendor=VENDOR,
            series="mx",
            model_range_code="$MDLX",
            model_range_description="Model X",
            model_code="$MTX13",
            model_description="Model X",
            line_code="$MTX13",
            line_description="Maximale Reichweite",
            line_option_codes=[
                LineItemOptionCode(
                    **{
                        "code": "$ICW00",
                        "description": "Premium-Innenraum Creme mit Walnuss Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": False,
                        "net_list_price": 2016.81,
                        "gross_list_price": 2400,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ST0Y",
                        "description": "Yoke-Lenkung",
                        "type": "STEERING_WHEEL",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APF2",
                        "description": "Volles Potenzial f\u00fcr autonomes Fahren",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 6302.52,
                        "gross_list_price": 7500,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSB",
                        "description": "Deep Blue Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1848.74,
                        "gross_list_price": 2200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PPSW",
                        "description": "Pearl White Multi-Coat",
                        "type": "PAINT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$ST03",
                        "description": "Lenkrad",
                        "type": "STEERING_WHEEL",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CC02",
                        "description": "6-Sitzer",
                        "type": "REAR_SEATS",
                        "included": False,
                        "net_list_price": 6470.59,
                        "gross_list_price": 7700,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PMNG",
                        "description": "Midnight Silver Metallic",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1848.74,
                        "gross_list_price": 2200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CC01",
                        "description": "5-Sitzer",
                        "type": "REAR_SEATS",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IBE00",
                        "description": "Komplett schwarz Premium-Innenraum mit Ebenholz Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CC04",
                        "description": "7-Sitzer",
                        "type": "REAR_SEATS",
                        "included": False,
                        "net_list_price": 3529.41,
                        "gross_list_price": 4200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$WX20",
                        "description": "22-Zoll Turbine-Felgen",
                        "type": "WHEELS",
                        "included": False,
                        "net_list_price": 4957.98,
                        "gross_list_price": 5900,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$WX00",
                        "description": "20-Zoll Cyberstream-Felgen",
                        "type": "WHEELS",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$SC04",
                        "description": "Supercharger-Abrechnung pro Nutzung",
                        "type": "SUPER_CHARGER",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PR01",
                        "description": "Ultra Red",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 2689.08,
                        "gross_list_price": 3200,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$IWW00",
                        "description": "Premium-Innenraum schwarz und wei\u00df mit Walnuss Dekor",
                        "type": "INTERIOR_COLORWAY",
                        "included": False,
                        "net_list_price": 2016.81,
                        "gross_list_price": 2400,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APPB",
                        "description": "Enhanced Autopilot",
                        "type": "AUTOPILOT",
                        "included": False,
                        "net_list_price": 3193.28,
                        "gross_list_price": 3800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$APBS",
                        "description": "Autopilot",
                        "type": "AUTOPILOT",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$PBSB",
                        "description": "Solid Black",
                        "type": "PAINT",
                        "included": False,
                        "net_list_price": 1512.61,
                        "gross_list_price": 1800,
                    }
                ),
                LineItemOptionCode(
                    **{
                        "code": "$CPF0",
                        "description": "Standard-Konnektivit\u00e4t",
                        "type": "CONNECTIVITY",
                        "included": True,
                        "net_list_price": 0.0,
                        "gross_list_price": 0,
                    }
                ),
            ],
            currency="EUR",
            net_list_price=101672.27,
            gross_list_price=120990,
            market=Market.DE,
        ),
    ]

    with open(f"{TEST_DATA_DIR}/modelx_de.html", "r") as payload:
        for item in parse_line_items(payload.read(), Market.DE):
            assert item in expected_models_line_items
            expected_line_item = expected_models_line_items[
                expected_models_line_items.index(item)
            ]
            item.line_option_codes.sort(key=lambda x: x.code)
            expected_line_item.line_option_codes.sort(key=lambda x: x.code)
            assert item == expected_line_item


def test_new_line_characters_remove_from_option_description():
    with open(f"{TEST_DATA_DIR}/modelx_de.html", "r") as payload:
        for item in parse_line_items(payload.read(), Market.DE):
            for line_option in item.line_option_codes:
                assert "\n" not in line_option.description


def test_get_line_description_returns_filtered_line_description():
    expected_result = "This is Line Description"
    line_description = "Model X This is Line Description"

    actual_result = get_line_description(line_description)

    assert actual_result == expected_result


def test_get_line_description_returns_filtered_line_description_for_fr_market():
    expected_result = "This is Line Description"
    line_description = "Model\xa0X This is Line Description"

    actual_result = get_line_description(line_description)

    assert actual_result == expected_result


def test_parse_model_and_series():
    expected_series = "mx"

    model, actual_series = parse_model_and_series("/de_de/modelx", Market.DE)

    assert expected_series == actual_series
    assert "modelx" == model


def test_parse_available_models_v2():
    expected_model_links = {
        "/de_de/models/design",
        "/de_de/modely/design",
        "/de_de/modelx/design",
        "/de_de/model3/design",
    }

    with open(f"{TEST_DATA_DIR}/tesla_homepage_v2.json", "r") as payload:
        assert parse_available_models_links(json.load(payload)) == expected_model_links


def test_adjust_otr_price():
    line_item = [create_test_line_item(line_code="mxt3")]
    actual_line_item = adjust_otr_price(line_item, {"mxt3": "$320"})
    assert actual_line_item[0].on_the_road_price == 320


def test_parse_otr_price_should_be_able_to_return_formated_price():
    expected_price = 3254500
    actual_price = parse_otr_price("$325,4500")
    assert actual_price == expected_price
