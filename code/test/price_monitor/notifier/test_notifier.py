import unittest
from test.price_monitor.utils.test_data_builder import create_difference_line_item
from unittest.mock import patch

from google.api_core.exceptions import Cancelled
from loguru import logger

from src.price_monitor.model.difference_item import DifferenceReason
from src.price_monitor.notifier.notifier import (
    Notifier,
    _merge_summaries,
    building_notifications_body_for_teams,
)
from src.price_monitor.utils.clock import today_dashed_str


class TestNotifier(unittest.TestCase):
    @patch("src.price_monitor.notifier.notifier.Notifier._notify_gchat")
    def test_notifier_does_not_calls_notify_gchat_when_no_channel_is_in_config(
        self, mock_notify_gchat
    ):
        notifier = Notifier({})
        differences_to_notify = [create_difference_line_item()]

        notifier.notify(differences_to_notify)

        mock_notify_gchat.assert_not_called()

    @patch("src.price_monitor.notifier.notifier.Notifier._notify_gchat")
    def test_notifier_calls_notify_gchat_when_gchat_channel_is_in_config(
        self, mock_notify_gchat
    ):
        config = {
            "notification": {
                "channels": {"gchat": {"gchat_url": "SECRETabc"}},
                "urls": {"dashboard_url": "testing.com"},
            }
        }

        notifier = Notifier(config)
        differences_to_notify = [create_difference_line_item()]

        notifier.notify(differences_to_notify)

        mock_notify_gchat.assert_called_with(
            "SECRETabc",
            f"\n*[Testing] Price monitor alert for {today_dashed_str()}*:\n\nAUDI changes:\n\tNL:\n\t\t_NEW_LINE : 1_\n\n\n",
            len(differences_to_notify),
        )

    @patch("src.price_monitor.notifier.notifier.Notifier._notify_teams")
    def test_notifier_calls_notify_and_fetch_secret_teams_when_teams_channel_is_in_config(
        self, mock_notify_teams
    ):
        config = {
            "notification": {
                "channels": {"teams": {"teams_webhook": "SECRETabc"}},
                "urls": {"dashboard_url": "testing.com"},
            }
        }
        notifier = Notifier(config)
        differences_to_notify = [create_difference_line_item()]

        notifier.notify(differences_to_notify)

        mock_notify_teams.assert_called_with("SECRETabc", differences_to_notify, [])

    @patch(
        "src.price_monitor.notifier.notifier.fetch_secret_if_present",
        side_effect=Cancelled("Error with API call"),
    )
    @patch.object(logger, "error")
    def test_notifier_logs_an_error_when_fetch_secret_is_present_returns_gcp_exception_for_gchat(
        self, mock_error, mock_fetch_secret_if_present
    ):
        config = {
            "notification": {
                "channels": {"gchat": {"gchat_url": "SECRETabc"}},
                "urls": {"dashboard_url": "testing.com"},
            }
        }

        notifier = Notifier(config)
        differences_to_notify = [create_difference_line_item()]

        notifier.notify(differences_to_notify)

        mock_error.assert_called_with(
            "GCP Exception retrieving secret from secret manager, secret: SECRETabc , error: Error with API call, None, 499"
        )

    @patch.object(Notifier, "_notify_gchat")
    @patch(
        "src.price_monitor.notifier.notifier.fetch_secret_if_present",
        side_effect=Exception("Unhandled"),
    )
    @patch.object(logger, "error")
    def test_notifier_logs_an_error_when_fetch_secret_is_present_returns_uknown_exception_for_gchat(
        self, mock_error, mock_fetch_secret_if_present, mock_notify_gchat
    ):
        config = {
            "notification": {
                "channels": {"gchat": {"gchat_url": "SECRETabc"}},
                "urls": {"dashboard_url": "testing.com"},
            }
        }

        notifier = Notifier(config)
        differences_to_notify = [create_difference_line_item()]

        notifier.notify(differences_to_notify)

        mock_error.assert_called_with(
            "Unknown exception retrieving secret from secret manager, secret: SECRETabc , error: Unhandled"
        )
        mock_notify_gchat.assert_not_called()

    @patch.object(Notifier, "_notify_teams")
    @patch(
        "src.price_monitor.notifier.notifier.fetch_secret_if_present",
        side_effect=Cancelled("Error with API call"),
    )
    @patch.object(logger, "error")
    def test_notifier_logs_an_error_when_fetch_secret_is_present_returns_gcp_exception_for_teams(
        self, mock_error, mock_fetch_secret_if_present, mock_notify_teams
    ):
        config = {
            "notification": {
                "channels": {"teams": {"teams_webhook": "teams_secret"}},
                "urls": {"dashboard_url": "testing.com"},
            }
        }

        notifier = Notifier(config)
        differences_to_notify = [create_difference_line_item()]

        notifier.notify(differences_to_notify)

        mock_error.assert_called_with(
            "GCP Exception retrieving secret from secret manager, secret: teams_secret , error: Error with API call, None, 499"
        )
        mock_notify_teams.assert_not_called()

    @patch(
        "src.price_monitor.notifier.notifier._format_price_changes_notification_for_gchat"
    )
    @patch("src.price_monitor.notifier.notifier.Notifier._notify_gchat")
    def test_notifier_does_not_call_notify_gchat_when_there_is_no_price_change(
        self, mock_notify_gchat, mock_format_price_changes_notification_for_gchat
    ):
        config = {
            "notification": {
                "channels": {"gchat": {"gchat_url": "SECRETabc"}},
                "urls": {"dashboard_url": "testing.com"},
            }
        }

        notifier = Notifier(config)
        differences_to_notify = []

        notifier.notify(differences_to_notify)

        mock_format_price_changes_notification_for_gchat.assert_not_called()

        mock_notify_gchat.assert_not_called()

    @patch("src.price_monitor.notifier.notifier._summarize_model_price_change")
    @patch("src.price_monitor.notifier.notifier.Notifier._notify_gchat")
    def test_notifier_calls_notify_gchat_when_there_is_price_change(
        self, mock_notify_gchat, mock_summarize_model_price_change
    ):
        config = {
            "notification": {
                "channels": {"gchat": {"gchat_url": "SECRETabc"}},
                "urls": {"dashboard_url": "testing.com"},
            }
        }

        mock_summarize_model_price_change.return_value = ""

        notifier = Notifier(config)
        differences_to_notify = [
            create_difference_line_item(reason=DifferenceReason.PRICE_CHANGE)
        ]

        notifier.notify(differences_to_notify)
        mock_summarize_model_price_change.assert_called_with(differences_to_notify)

        mock_notify_gchat.assert_called_with(
            "SECRETabc",
            f"\n*[Testing] Price monitor alert for {today_dashed_str()}*:\n\nAUDI changes:\n\tNL:\n\t\t_PRICE_CHANGE : 1_\n\n\n",
            1,
        )

    @patch(
        "src.price_monitor.notifier.notifier.building_price_changes_notifications_body_for_gchat"
    )
    @patch("src.price_monitor.notifier.notifier.Notifier._notify_gchat")
    def test_notifier_calls_format_price_changes_notification_for_gchat_when_there_is_price_change(
        self,
        mock_notify_gchat,
        mock_building_price_changes_notifications_body_for_gchat,
    ):
        config = {
            "notification": {
                "channels": {"gchat": {"gchat_url": "SECRETabc"}},
                "urls": {"dashboard_url": "testing.com"},
            }
        }

        mock_building_price_changes_notifications_body_for_gchat.return_value = "AUDI Price Changes:\n\tNL:\n\t\tMODEL NAME : model line\n\t\tOLD PRICE : 10.00 Eur\n\t\tNEW PRICE : 20.00\n\t\t% OF CHANGE : 100%\n\n"

        notifier = Notifier(config)
        differences_to_notify = [
            create_difference_line_item(
                model_description="model",
                line_description="line",
                old_value="10.00",
                new_value="20.00",
                reason=DifferenceReason.PRICE_CHANGE,
            )
        ]

        notifier.notify(differences_to_notify)
        mock_building_price_changes_notifications_body_for_gchat.assert_called_with(
            {
                "audi": {
                    "NL": [
                        {
                            "MODEL NAME": "model line",
                            "OLD PRICE": "10.0 €",
                            "NEW PRICE": "20.0 €",
                            "% OF CHANGE": "100.0% ↑",
                        }
                    ]
                }
            }
        )

        mock_notify_gchat.assert_called_with(
            "SECRETabc",
            f"\n*[Testing] Price monitor alert for {today_dashed_str()}*:\n\nAUDI Price Changes:\n\tNL:\n\t\tMODEL NAME : model line\n\t\tOLD PRICE : 10.00 Eur\n\t\tNEW PRICE : 20.00\n\t\t% OF CHANGE : 100%\n\n\n",
            1,
        )

    @patch("src.price_monitor.notifier.notifier._merge_summaries")
    def test_notify_teams_calls_merge_summaries_when_there_is_price_change(
        self, mock_merge_summaries
    ):
        config = {
            "notification": {
                "channels": {"teams": {"teams_webhook": "SECRETabc"}},
                "urls": {"dashboard_url": "testing.com"},
            }
        }
        notifier = Notifier(config)
        differences_to_notify = [
            create_difference_line_item(
                model_description="model",
                line_description="line",
                old_value="10.00",
                new_value="20.00",
                reason=DifferenceReason.PRICE_CHANGE,
            )
        ]
        notifier.notify(differences_to_notify)

        mock_merge_summaries.assert_called_with(
            {
                "audi": {
                    "NL": [
                        {
                            "MODEL NAME": "model line",
                            "OLD PRICE": "10.0 €",
                            "NEW PRICE": "20.0 €",
                            "% OF CHANGE": "100.0% ↑",
                        }
                    ]
                }
            },
            {"audi": {"NL": {"PRICE_CHANGE": 1}}},
        )

    @patch("src.price_monitor.notifier.notifier._merge_summaries")
    def test_notify_teams_does_not_calls_merge_summaries_when_there_are_only_line_changes(
        self, mock_merge_summaries
    ):
        config = {
            "notification": {
                "channels": {"teams": {"teams_webhook": "SECRETabc"}},
                "urls": {"dashboard_url": "testing.com"},
            }
        }
        notifier = Notifier(config)
        differences_to_notify = [
            create_difference_line_item(
                model_description="model",
                line_description="line",
                old_value="10.00",
                new_value="20.00",
                reason=DifferenceReason.NEW_LINE,
            )
        ]
        notifier.notify(differences_to_notify)

        mock_merge_summaries.assert_not_called()

    def test_building_notifications_body_for_teams_when_there_are_both_line_and_price_changes(
        self,
    ):
        merged_summary = {
            "audi": {
                "NL": {
                    "PRICE_CHANGE": [
                        {
                            "MODEL NAME": "model line",
                            "OLD PRICE": "10.0 €",
                            "NEW PRICE": "20.0 €",
                            "% OF CHANGE": "100.0% ↑",
                        }
                    ],
                    "NEW_LINE": 1,
                }
            }
        }
        expected_result = "```\nAUDI changes:\n\tNL:\n\t\tPRICE_CHANGE:\n\t\t\tMODEL NAME : model line\n\t\t\tOLD PRICE : 10.0 €\n\t\t\tNEW PRICE : 20.0 €\n\t\t\t% OF CHANGE : 100.0% ↑\n\n\t\t-----------------------------------------------\n\t\tNEW_LINE: 1\n\n```"

        actual_result = building_notifications_body_for_teams(merged_summary)
        assert expected_result == actual_result

    def test_merge_summaries_when_there_are_both_line_and_price_changes(
        self,
    ):
        line_summary = {"audi": {"NL": {"PRICE_CHANGE": 1, "NEW_LINE": 1}}}
        price_summary = {
            "audi": {
                "NL": [
                    {
                        "MODEL NAME": "model line",
                        "OLD PRICE": "10.0 €",
                        "NEW PRICE": "20.0 €",
                        "% OF CHANGE": "100.0% ↑",
                    }
                ]
            }
        }
        expected_result = {
            "audi": {
                "NL": {
                    "PRICE_CHANGE": [
                        {
                            "MODEL NAME": "model line",
                            "OLD PRICE": "10.0 €",
                            "NEW PRICE": "20.0 €",
                            "% OF CHANGE": "100.0% ↑",
                        }
                    ],
                    "NEW_LINE": 1,
                }
            }
        }

        actual_result = _merge_summaries(price_summary, line_summary)

        assert expected_result == actual_result
