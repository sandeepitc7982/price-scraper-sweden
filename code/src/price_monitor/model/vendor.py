from enum import Enum, auto

from strenum import StrEnum


class Vendor(StrEnum):
    BMW = "bmw"
    TESLA = "tesla"
    AUDI = "audi"
    MERCEDES_BENZ = "mercedes_benz"


class Market(StrEnum):
    DE = auto()
    FR = auto()
    AU = auto()
    AT = auto()
    NL = auto()
    US = auto()
    UK = auto()
    SE = auto()


class MarketVAT(Enum):
    DE = 19
    NL = 21
    FR = 20
    AU = 10
    AT = 20
    US = 0
    UK = 20
    SE = 25


class Currency(StrEnum):
    DE = "EUR"
    FR = "EUR"
    NL = "EUR"
    AT = "EUR"
    US = "USD"
    UK = "GBP"
    AU = "AUD"
    SE = "SEK"


def compute_net_list_price(market: Market, gross_list_price: float) -> float:
    return round(gross_list_price / (1 + (MarketVAT[market].value / 100)), 2)
