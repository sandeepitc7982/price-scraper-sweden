from pathlib import Path
from typing import Annotated, Optional

import typer

from src.price_monitor.bootstrap import initialize, finalize
from src.price_monitor.finance_scraper.main_finance_scraper import scrape_finance
from src.price_monitor.model.difference_item import DifferenceItem
from src.price_monitor.model.vendor import Market, Vendor
from src.price_monitor.price_comparer.comparator import Comparator
from src.price_monitor.data_quality.data_quality_checks import DataQualityCheck
from src.price_monitor.data_quality.data_quality_checks_finance import (
    DataQualityCheckFinance,
)
from src.price_monitor.data_quality.finance_data_quality_processor import (
    FinanceDataQualityProcessor,
)
from src.price_monitor.finance_comparer.finance_options_comparator import (
    FinanceOptionsComparator,
)
from src.price_monitor.notifier.notifier import Notifier
from src.price_monitor.repository.difference_item_repository import (
    DifferenceItemRepository,
)
from src.price_monitor.repository.finance_item_repository import (
    FileSystemFinanceLineItemRepository,
)
from src.price_monitor.repository.line_item_repository import (
    FileSystemLineItemRepository,
)
from src.price_monitor.price_scraper.main_scraper import scrape
from src.price_monitor.utils.clock import today_dashed_str_with_key
from src.price_monitor.utils.output_format import OutputFormat

app = typer.Typer(no_args_is_help=True, help="Price Monitor CLI Application")


@app.command(rich_help_panel="Scrapers")
def run_scraper(
    config_file: Annotated[
        Path, typer.Option(help="File path to a json config", exists=True)
    ],
    scraper: Annotated[
        Optional[Vendor],
        typer.Option(
            help="Run one scraper from the supported scrapers",
            rich_help_panel="Filters",
        ),
    ] = None,
    market: Annotated[
        Optional[Market],
        typer.Option(
            help="Scrape one market from the supported markets",
            rich_help_panel="Filters",
        ),
    ] = None,
    output: Annotated[
        Optional[OutputFormat],
        typer.Option(
            help="Set the output file format",
            rich_help_panel="Output",
        ),
    ] = None,
    directory: Annotated[
        Optional[str],
        typer.Option(help="Set the output file directory", rich_help_panel="Output"),
    ] = None,
):
    """
    Runs the price scraper and saves the scraped data to a local directory in the specified file format.
    """
    config, adls = initialize(
        config_file=config_file,
        directory=directory,
        market=market,
        output=output,
        scraper=scraper,
    )

    scrape(
        config,
        FileSystemLineItemRepository(config=config),
    )

    finalize(adls)


@app.command(rich_help_panel="Scrapers")
def run_finance_scraper(
    config_file: Annotated[
        Path, typer.Option(help="File path to a json config", exists=True)
    ],
    scraper: Annotated[
        Optional[Vendor],
        typer.Option(
            help="Run one scraper from the supported scrapers",
            rich_help_panel="Filters",
        ),
    ] = None,
    market: Annotated[
        Optional[Market],
        typer.Option(
            help="Scrape one market from the supported markets",
            rich_help_panel="Filters",
        ),
    ] = None,
    output: Annotated[
        Optional[OutputFormat],
        typer.Option(
            help="Set the output file format",
            rich_help_panel="Output",
        ),
    ] = None,
    directory: Annotated[
        Optional[str],
        typer.Option(help="Set the output file directory", rich_help_panel="Output"),
    ] = None,
):
    """
    Runs the finance scraper and saves the scraped data to a local directory in the specified file format.
    """
    config, adls = initialize(
        config_file=config_file,
        directory=directory,
        market=market,
        output=output,
        finance_scraper=scraper,
    )

    scrape_finance(
        config,
        FileSystemFinanceLineItemRepository(config=config),
    )

    finalize(adls)


@app.command(rich_help_panel="Comparers")
def run_compare(
    config_file: Annotated[
        Path, typer.Option(help="File path to a json config", exists=True)
    ],
    output: Annotated[
        Optional[OutputFormat] | None,
        typer.Option(
            help="Set the output file format",
            rich_help_panel="Output",
        ),
    ] = None,
    directory: Annotated[
        Optional[str],
        typer.Option(help="Set the output file directory", rich_help_panel="Output"),
    ] = None,
):
    """
    Runs the price comparator and produces a changelog of differences between today and yesterday's data.
    """
    config, adls = initialize(
        config_file=config_file, directory=directory, output=output
    )

    Comparator(config).compare()

    finalize(adls)


@app.command(rich_help_panel="Comparers")
def run_finance_compare(
    config_file: Annotated[
        Path, typer.Option(help="File path to a json config", exists=True)
    ],
    output: Annotated[
        Optional[OutputFormat] | None,
        typer.Option(
            help="Set the output file format",
            rich_help_panel="Output",
        ),
    ] = None,
    directory: Annotated[
        Optional[str],
        typer.Option(help="Set the output file directory", rich_help_panel="Output"),
    ] = None,
):
    """
    Runs the Finance comparator and produces a changelog of differences between today and yesterday's data.
    """
    config, adls = initialize(
        config_file=config_file, directory=directory, output=output
    )

    FinanceOptionsComparator(config).compare()

    finalize(adls)


@app.command(rich_help_panel="Notifiers")
def notify(
    config_file: Annotated[
        Path, typer.Option(help="File path to a json config", exists=True)
    ],
    directory: Annotated[
        Optional[str],
        typer.Option(help="Set the output file directory", rich_help_panel="Output"),
    ] = None,
):
    """
    Sends a notification to the configured destinations if a changelog is detected for the current day.
    """
    config, adls = initialize(config_file=config_file, directory=directory)
    if "notification" not in config:
        return

    notifier = Notifier(config=config)
    difference_repository = DifferenceItemRepository(config=config)
    differences = difference_repository.load(
        date=today_dashed_str_with_key(), difference_item_class=DifferenceItem
    )

    notifier.notify(differences=differences)


@app.command(rich_help_panel="Processors")
def check_data_quality(
    config_file: Annotated[
        Path, typer.Option(help="File path to a json config", exists=True)
    ],
    directory: Annotated[
        Optional[str],
        typer.Option(help="Set the output file directory", rich_help_panel="Output"),
    ] = None,
):
    """
    Checks for data quality issues and logs its findings.
    """
    config, adls = initialize(config_file=config_file, directory=directory)
    line_item_repository = FileSystemLineItemRepository(config=config)
    finance_line_item_repository = FileSystemFinanceLineItemRepository(config=config)
    data_quality = DataQualityCheck(line_item_repository)
    finance_data_quality = DataQualityCheckFinance(finance_line_item_repository)
    data_quality.run_quality_checks_all_vendors(config)
    finance_data_quality.run_quality_checks_all_vendors(config)
    # Data quality checks are triggered below
    loader = FinanceDataQualityProcessor(finance_line_item_repository, config=config)
    loader.run_quality_checks_all_vendors(config)

    finalize(adls)


if __name__ == "__main__":
    app()
