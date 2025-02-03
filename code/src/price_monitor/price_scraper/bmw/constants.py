from src.price_monitor.model.vendor import Market

BASE_URL = "https://prod.ucp.bmw.cloud"
MARKET_MAP = {
    Market.DE: "de",
    Market.FR: "fr",
    Market.AT: "at",
    Market.NL: "nl",
    Market.UK: "gb",
    Market.SE: "se"
}

KW_UNIT = " kW"
HP_UNIT = " hp"

SWEDEN_G45_DESC = "BMW X3"

MODEL_MATRICES_PATH = (
    "/model-matrices/vehicle-trees/connext-bmw/sources/pcaso/brands/bmwCar/countries"
)
LOCALISATION_PATH = (
    "/localisations/overridden-vehicle-data/sources/pcaso/brands/bmwCar/countries"
)
PUBLIC_PRICING_PATH = "/pricing/calculation/public-calculation/price-lists/pcaso,con/brands/bmwCar/countries"
CONSTRUCTIBILITY_PATH = "/rulesolver/constructibility-check/configuration-state"
CONFIGURATION_STATE_PATH = (
    "/rulesolver/constructibility-check/rule-sets/pcaso,con/brands/bmwCar/countries"
)
API_KEY_URL = "https://configure.bmw.de/de_DE/configure/F40?icp=de_s_con_f40"


# Below links specific to US market.
USA_MODEL_LIST_URL = "https://configure.bmwusa.com/UBYOConfigurator/v4/BM/modellist"
USA_MODEL_CONFIGURATION_URL = (
    "https://configure.bmwusa.com/UBYOConfigurator/v4/configuration"
)
X_API_KEY = "x-api-key"
