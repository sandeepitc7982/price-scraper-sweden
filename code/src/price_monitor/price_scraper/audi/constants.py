from src.price_monitor.model.vendor import Market

AUDI_MARKET_MAP = {
    Market.DE: "de",
}

AUDI_BASE_URL = "https://www.audi.de"
DE_CONFIG_URL = "https://www.audi.de/ak4/bin/dpu-de/configuration?context=nemo-de%3Ade"

INCLUSION_AND_TYPE_URL = (
    "https://onegraph.audi.com/graphql?operationName=EquipmentCategories"
)

REQUEST_TIMEOUT_SECONDS = 120


AUDI_USA_BASE_URL = "https://www.audiusa.com"

AUDI_USA_CONFIG_URL = "https://www.audiusa.com/ak4/bin/dpu-us/stateless-configuration?context=nemo-us%3Aus-en"

AUDI_UK_BASE_URL = "https://www.audi.co.uk"
AUDI_UK_CONFIG_URL = (
    "https://www.audi.co.uk/ak4/bin/dpu-uk/configuration?context=nemo-uk%3Agb-en"
)
AUDI_CAR_INFO_URL = "https://www.audi.co.uk/uk/web/en/models/"

DEAD_OPTION_STATUS = "00000"
DEAD_OPTION_TYPE = ["equipmentcontent", "model", "trimline", "accessory", "accessories"]
INCLUDED_OPTION_STATUS = ["11010", "10011"]

COMMON_OPTION_TYPE = ["Exterior Colors", "Räder & Reifen"]
