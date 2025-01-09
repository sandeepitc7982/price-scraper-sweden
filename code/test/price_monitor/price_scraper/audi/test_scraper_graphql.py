import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.price_monitor.price_scraper.audi.scraper_graphql import (
    build_option_type_url,
    get_option_type_details,
)

TEST_DATA_DIR = f"{Path(__file__).parent}/sample"


@patch("src.price_monitor.price_scraper.audi.scraper_graphql.execute_request")
def test_get_option_type_details_when_api_execute_successful_then_return_json_response(
    mock_execute_request,
):
    mock_session = Mock()
    carinfo = json.loads(
        open(f"{TEST_DATA_DIR}/etron_option_common_details.json").read()
    )
    mock_execute_request.return_value = "option_type_details"

    response = get_option_type_details(carinfo=carinfo, session=mock_session)

    assert response == "option_type_details"
    mock_execute_request.assert_called_with(
        "get",
        "https://onegraph.audi.com/graphql?operationName=EquipmentCategories&variables=%7B%22configuredCarIdentifier%22%3A%20%7B%22brand%22%3A%20%22A%22%2C%20%22country%22%3A%20%22DE%22%2C%20%22language%22%3A%20%22de%22%2C%20%22model%22%3A%20%7B%22year%22%3A%202024%2C%20%22version%22%3A%200%2C%20%22code%22%3A%20%22F83RJ7%22%2C%20%22extensions%22%3A%20%5B%22%22%5D%7D%2C%20%22exteriorColor%22%3A%20%226Y6Y%22%2C%20%22interiorColor%22%3A%20%22JN%22%7D%7D&extensions=%7B%22colaDataVersions%22%3A%20%228f47c3205101569fa2350282f93e47c4dc200091413f0a24922f65c1bb24abc0%22%2C%20%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%228ef5c490efb19af8fa1951b8cf2a17b039c5ddda36b6d8446bbd948434623f77%22%7D%7D",
        mock_session,
        headers={
            "apollographql-client-name": "3bb6bf8e-9d21-4462-b2c2-7b8983236eb5_via_@volkswagen-onehub/audi-cola-service_3.5.2",
            "apollographql-client-version": "unknown",
        },
    )


@patch("src.price_monitor.price_scraper.audi.scraper_graphql.build_option_type_url")
@patch("src.price_monitor.price_scraper.audi.scraper_graphql.execute_request")
def test_get_option_type_details_when_api_execute_fails_then_raise_exception(
    mock_execute_request, mock_build_option_type_url
):
    mock_session = Mock()
    mock_execute_request.return_value = {"errors": "something went wrong."}
    mock_build_option_type_url.return_value = "option_type_url"

    with pytest.raises(ValueError):
        get_option_type_details(carinfo="carinfo", session=mock_session)


def test_build_option_type_url():
    expected_url = "https://onegraph.audi.com/graphql?operationName=EquipmentCategories&variables=%7B%22configuredCarIdentifier%22%3A%20%7B%22brand%22%3A%20%22A%22%2C%20%22country%22%3A%20%22DE%22%2C%20%22language%22%3A%20%22de%22%2C%20%22model%22%3A%20%7B%22year%22%3A%202024%2C%20%22version%22%3A%200%2C%20%22code%22%3A%20%22F83RJ7%22%2C%20%22extensions%22%3A%20%5B%22%22%5D%7D%2C%20%22exteriorColor%22%3A%20%226Y6Y%22%2C%20%22interiorColor%22%3A%20%22JN%22%7D%7D&extensions=%7B%22colaDataVersions%22%3A%20%228f47c3205101569fa2350282f93e47c4dc200091413f0a24922f65c1bb24abc0%22%2C%20%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%228ef5c490efb19af8fa1951b8cf2a17b039c5ddda36b6d8446bbd948434623f77%22%7D%7D"
    carinfo = json.loads(
        open(f"{TEST_DATA_DIR}/etron_option_common_details.json").read()
    )
    actual_url = build_option_type_url(carinfo=carinfo)

    assert expected_url == actual_url
