from src.price_monitor.model.vendor import Market

BASE_URL = "https://www.tesla.com"
MARKET_MAP = {
    Market.DE: "de_de",
    Market.NL: "nl_nl",
    Market.FR: "fr_fr",
    Market.AU: "en_au",
    Market.AT: "de_at",
    Market.US: "",
    Market.UK: "en_gb",
    Market.SE: "sv_se"
}
MODELS = ["Model Y", "Model X", "Model 3", "Model S"]
