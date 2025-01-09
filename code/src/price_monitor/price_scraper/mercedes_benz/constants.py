from src.price_monitor.model.vendor import Market

BASE_URL = "https://api.oneweb.mercedes-benz.com/vmds-api/v1/vehicles/"
MARKET_MAP_BASE_URL = {Market.DE: "DE/de", Market.UK: "GB/en", Market.SE: "SE/sv"}

MARKET_MAP_MODEL_SERIES_URL = {
    Market.DE: "de_DE",
    Market.UK: "en_GB",
    Market.SE: "sv_SE",
}

MODEL_SERIES_URL = "https://configurator.mercedes-benz.com/cc-backend/api/v3/"

BASE_URL_USA = "https://www.mbusa.com"

HASH_VALUE_FOR_MODEL_SERIES_URL = "%23"
