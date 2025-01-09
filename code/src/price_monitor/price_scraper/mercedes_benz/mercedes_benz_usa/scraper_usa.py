from loguru import logger
from requests import Session

from src.price_monitor.model.line_item import LineItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.parser_usa import (
    AvailableModel,
    MercedesBenzUSAParser,
)
from src.price_monitor.price_scraper.mercedes_benz.mercedes_benz_usa.scraper_usa_api import (
    execute_all_models_request,
    execute_model_request,
)
from src.price_monitor.utils.clock import yesterday_dashed_str


class MercedesBenzUSAScraper:
    def __init__(
        self,
        line_item_repository: FileSystemLineItemRepository,
        session: Session,
        config: dict,
    ):
        self.market = Market.US
        self.vendor = Vendor.MERCEDES_BENZ
        self.parser = MercedesBenzUSAParser()
        self.line_item_repository = line_item_repository
        self.session = session
        self.config = config

    def scrape_models(self) -> list[LineItem]:
        scraped_models = []
        all_models = self._get_models()

        for model in all_models:
            if model.line_exists:
                scraped_models.extend(self._get_trim_lines(model))
            elif not model.line_exists:
                model_item = self._get_basic_line(model)
                if model_item:
                    scraped_models.append(model_item)
            # TODO: Why?
            if self.config.get("e2e_tests"):
                break
        return scraped_models

    def _get_trim_lines(self, model: AvailableModel) -> [LineItem]:
        model_page = execute_model_request(model.build_page, self.session)
        trim_lines = []

        if model_page:
            line_code_resource_list = self.parser.parse_line_codes(model_page)
            for trim_code in line_code_resource_list:
                logger.info(
                    f"[{self.market}] Scraping {trim_code.line_description} Line for model {model.model_code}"
                )
                trim_line = self._get_trim_line(
                    trim_code.line_path,
                    trim_code.line_description,
                    trim_code.line_code,
                )
                if not trim_line:
                    trim_line = self.line_item_repository.load_line_item_for_trim_line(
                        date=yesterday_dashed_str(),
                        market=self.market,
                        vendor=self.vendor,
                        model_code=model.model_code,
                        line_code=trim_code.line_code,
                    )
                trim_lines.append(trim_line)

        if len(trim_lines) == 0:
            trim_lines = self._load_previous_day_line_items(model)

        return trim_lines

    def _get_basic_line(self, model: AvailableModel) -> LineItem:
        model_data = self._get_trim_line(model.build_page, "BASIC_LINE", "")
        if model_data:
            logger.info(
                f"[{self.market}] Scraping BASIC LINE for {model_data.model_description}"
            )
        else:
            model_data = self._load_previous_day_line_items(model)
            if len(model_data) > 0:
                return model_data[0]
        return model_data

    def _get_trim_line(
        self, path: str, line_description: str, line_code: str
    ) -> list[LineItem]:
        model_page = execute_model_request(path, self.session)
        if model_page:
            return self.parser.parse_trim_line(model_page, line_description, line_code)
        return []

    def _load_previous_day_line_items(self, model: AvailableModel) -> list[LineItem]:
        logger.error(
            f"[{self.market}] Loading previous day data for model {model.build_page}"
        )
        items = self.line_item_repository.load_model_filter_by_model_code(
            date=yesterday_dashed_str(),
            market=self.market,
            vendor=self.vendor,
            model_code=model.model_code,
        )

        if items:
            logger.warning(
                f"[{self.market}] Loaded {len(items)} items from previous day"
            )
        else:
            logger.error(
                f"[{self.market}] Got zero line items for model {model.build_page}"
            )
        return items

    def _get_models(self) -> list[AvailableModel]:
        all_models_response = execute_all_models_request(self.session)
        if not all_models_response:
            return []
        else:
            return self.parser.parse_available_models(all_models_response)
