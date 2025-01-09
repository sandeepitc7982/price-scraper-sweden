import requests
from google.api_core.exceptions import GoogleAPICallError
from loguru import logger
from pymsteams import cardsection, connectorcard

from src.price_monitor.model.difference_item import DifferenceItem, DifferenceReason
from src.price_monitor.model.vendor import Currency
from src.price_monitor.price_scraper.constants import CURRENCY_SYMBOLS
from src.price_monitor.utils.clock import today_dashed_str
from src.price_monitor.utils.secret_service import fetch_secret_if_present


def _summarize_model_price_change(differences: list[DifferenceItem]) -> dict:
    price_difference_summary = {}
    for diff in differences:
        perc_diff = (
            (float(diff.new_value) - float(diff.old_value))
            / float(diff.old_value)
            * 100
        )
        vendor = price_difference_summary.get(diff.vendor, dict())
        market = vendor.get(diff.market, [])
        symbol = CURRENCY_SYMBOLS[Currency[diff.market].value]
        if perc_diff > 0:
            arrow = "↑"
        else:
            arrow = "↓"
        market.append(
            {
                "MODEL NAME": f"{diff.model_description.strip()} {diff.line_description.strip()}",
                "OLD PRICE": f"{_format_price(diff.old_value)} {symbol}",
                "NEW PRICE": f"{_format_price(diff.new_value)} {symbol}",
                "% OF CHANGE": f"{round(perc_diff, 2)}% {arrow}",
            }
        )
        vendor[diff.market] = market
        price_difference_summary[diff.vendor] = vendor
    return price_difference_summary


def _format_price(value) -> str:
    return "{:,}".format(float(value))


def _summarize_differences(differences: list[DifferenceItem]) -> dict:
    """
    Summarizes the list of differences into a map of:
    [Vendor] -> [Market] -> [DifferenceReason] -> counter
    """
    result = dict()
    unique_option_added = "unique option added"
    unique_option_removed = "unique option removed"

    for element in differences:
        vendor = result.get(element.vendor, dict())
        market = vendor.get(element.market, dict())
        if element.reason == DifferenceReason.OPTION_ADDED:
            _summarize_option_change(element.new_value, market, unique_option_added)
        elif element.reason == DifferenceReason.OPTION_REMOVED:
            _summarize_option_change(element.old_value, market, unique_option_removed)
        else:
            market[element.reason] = market.get(element.reason, 0) + 1
        vendor[element.market] = market
        result[element.vendor] = vendor

    _update_summary(result, unique_option_added, unique_option_removed)
    return result


def _update_summary(result, unique_option_added, unique_option_removed):
    for vendor, markets in result.items():
        for market, reasons in markets.items():
            if unique_option_added in list(reasons.keys()):
                _update_option_changes(
                    market,
                    markets,
                    reasons,
                    DifferenceReason.OPTION_ADDED,
                    unique_option_added,
                )
            if unique_option_removed in list(reasons.keys()):
                _update_option_changes(
                    market,
                    markets,
                    reasons,
                    DifferenceReason.OPTION_REMOVED,
                    unique_option_removed,
                )


def _update_option_changes(market, markets, reasons, reason, unique_option_change):
    markets[market][reason] = len(reasons[unique_option_change])
    del reasons[unique_option_change]


def _summarize_option_change(value, market, unique_option_change):
    option_change = market.get(unique_option_change, dict())
    option_change[value] = option_change.get(value, 0) + 1
    market[unique_option_change] = option_change


def _format_price_changes_notification_for_gchat(
    differences: list[DifferenceItem], environment: str
) -> str:
    summary = _summarize_model_price_change(differences)
    body = building_price_changes_notifications_body_for_gchat(summary)
    return f"""
*[{environment}] Price monitor alert for {today_dashed_str()}*:

{body}
"""


def _merge_summaries(price_summary, line_summary):
    for vendor, markets in price_summary.items():
        for market, models in markets.items():
            line_summary[vendor][market]["PRICE_CHANGE"] = models
    return line_summary


def building_price_changes_notifications_body_for_gchat(summary: dict):
    body = ""
    for vendor, stats in summary.items():
        body += f"{vendor.upper()} PRICE CHANGES:\n"
        for market, models in stats.items():
            body += f"\t{market}:\n"
            for model in models:
                for data, value in model.items():
                    body += f"\t\t*{data}* : {value}\n"
                body += "\n"
        body += "\n"

    return body


def building_notifications_body_for_teams(summary: dict):
    body = "\n"
    for vendor, stats in summary.items():
        body += f"{vendor.upper()} changes:\n"
        for market, reasons in stats.items():
            body += f"\t{market}:\n"
            for reason in reasons:
                if reason == "PRICE_CHANGE":
                    body += f"\t\t{reason}:\n"
                    for model in reasons[reason]:
                        for data, value in model.items():
                            body += f"\t\t\t{data} : {value}\n"
                        body += "\n"
                    body += "\t\t-----------------------------------------------\n"
                else:
                    body += f"\t\t{reason}: {reasons[reason]}\n"
        body += "\n"
    body = "```" + body + "```"

    return body


def _format_notification_for_gchat(
    differences: list[DifferenceItem], environment: str
) -> str:
    summary = _summarize_differences(differences)
    body = building_notifications_body_for_gchat(summary)
    return f"""
*[{environment}] Price monitor alert for {today_dashed_str()}*:

{body}
"""


def building_notifications_body_for_gchat(summary: dict):
    body = ""
    for vendor, stats in summary.items():
        body += f"{vendor.upper()} changes:\n"
        for market, reasons in stats.items():
            body += f"\t{market}:\n"
            for reason in reasons:
                body += f"\t\t_{reason} : {reasons[reason]}_\n"

        body += "\n"

    return body


class Notifier:
    def __init__(self, config: dict):
        self.channels = config.get("notification", {}).get("channels", {})
        self._gchat_channel = self.channels.get("gchat")
        self._teams_channel = self.channels.get("teams")
        self._dashbaord_url = (
            config.get("notification", {}).get("urls", {}).get("dashboard_url")
        )
        self.environment = config.get("environment", "Testing")

    def notify(self, differences: list[DifferenceItem]) -> None:
        if len(differences) == 0:
            return

        price_differences = list(
            filter(
                lambda difference: difference.reason == DifferenceReason.PRICE_CHANGE,
                differences,
            )
        )
        teams_differences = list(
            filter(
                lambda difference: difference.reason == DifferenceReason.PRICE_CHANGE
                or difference.reason == DifferenceReason.LINE_REMOVED
                or difference.reason == DifferenceReason.NEW_LINE,
                differences,
            )
        )

        try:
            channel_secret = ""
            if self._gchat_channel:
                channel_secret = self._gchat_channel.get("gchat_url", "")
                gchat_url = fetch_secret_if_present(secret=channel_secret)
                self._notify_gchat(
                    gchat_url,
                    _format_notification_for_gchat(differences, self.environment),
                    len(differences),
                )
                if len(price_differences) != 0 and len(price_differences) < 50:
                    self._notify_gchat(
                        gchat_url,
                        _format_price_changes_notification_for_gchat(
                            price_differences, self.environment
                        ),
                        len(price_differences),
                    )

            if self._teams_channel:
                channel_secret = self._teams_channel.get("teams_webhook", "")
                teams_webhook = fetch_secret_if_present(secret=channel_secret)
                self._notify_teams(teams_webhook, teams_differences, price_differences)

        except GoogleAPICallError as e:
            logger.error(
                f"GCP Exception retrieving secret from secret manager, secret: {channel_secret} , error: {e.message}, {e.reason}, {e.code}"
            )
        except Exception as e:
            logger.error(
                f"Unknown exception retrieving secret from secret manager, secret: {channel_secret} , error: {e}"
            )

    def _notify_gchat(self, gchat_url, message, length) -> None:
        requests.post(
            url=gchat_url,
            headers={"Content-Type": "application/json; charset=UTF-8"},
            json={"text": message},
        )

        logger.info(f"Sent Gchat notification for {length} differences")

    def _notify_teams(
        self,
        teams_webhook,
        differences: list[DifferenceItem],
        price_differences: list[DifferenceItem],
    ):
        teams_notification = connectorcard(teams_webhook)
        line_summary = _summarize_differences(differences)
        if len(price_differences) != 0 and len(price_differences) < 50:
            price_summary = _summarize_model_price_change(price_differences)
            merged_summary = _merge_summaries(price_summary, line_summary)
        else:
            merged_summary = line_summary

        body = building_notifications_body_for_teams(merged_summary)

        notification_section = cardsection()
        notification_section.activityTitle(
            f"""Price monitor notification for {today_dashed_str()}*"""
        )
        notification_section.activityText(body)

        teams_notification.addSection(notification_section)
        teams_notification.addLinkButton("Go to Dashboard", self._dashbaord_url)
        teams_notification.summary("This is from price scraper team")
        teams_notification.send()

        logger.info(f"Sent teams notification for {len(differences)} differences")
