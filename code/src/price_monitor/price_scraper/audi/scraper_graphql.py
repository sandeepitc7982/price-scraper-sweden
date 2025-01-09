import json
import urllib

from requests import Session

from src.price_monitor.price_scraper.audi.constants import INCLUSION_AND_TYPE_URL
from src.price_monitor.utils.caller import execute_request


def get_option_type_details(carinfo: dict, session: Session) -> dict:
    headers = {
        "apollographql-client-name": "3bb6bf8e-9d21-4462-b2c2-7b8983236eb5_via_@volkswagen-onehub/audi-cola-service_3.5.2",
        "apollographql-client-version": "unknown",
    }
    url = build_option_type_url(carinfo)

    details_json = execute_request("get", url, session, headers=headers)
    if "errors" in details_json:
        raise ValueError(details_json)
    return details_json


def build_option_type_url(carinfo):
    extra_options = carinfo["configuration"]["items"]
    ave = carinfo["configuration"]["ave"]
    basic_options = ave.split(",")[1:5]
    # API Parameters.
    variables = {
        "configuredCarIdentifier": {
            "brand": "A",
            "country": "DE",
            "language": "de",
            "model": {
                "year": int(basic_options[1]),
                "version": int(extra_options[0][6]),
                "code": basic_options[0],
                "extensions": [extra_options[0].split("_")[0][7:]],
            },
            "exteriorColor": basic_options[2],
            "interiorColor": basic_options[3],
        }
    }
    extensions = {
        "colaDataVersions": "8f47c3205101569fa2350282f93e47c4dc200091413f0a24922f65c1bb24abc0",
        "persistedQuery": {
            "version": 1,
            "sha256Hash": "8ef5c490efb19af8fa1951b8cf2a17b039c5ddda36b6d8446bbd948434623f77",
        },
    }
    # Converting dictionary into URL pattern.
    extensions_str = urllib.parse.quote(json.dumps(extensions), safe="")
    variables_str = urllib.parse.quote(json.dumps(variables), safe="")
    url = f"{INCLUSION_AND_TYPE_URL}&variables={variables_str}&extensions={extensions_str}"
    return url
