## Price Comparator Notifications
We provide notifications for the list of detected changes we get 
from Price Comparator by using [DifferenceItem](src/price_monitor/model/difference_item.py) dataset

## Notification Service

This service is run using the `notify` command. It sends summarized changes of Prices data to the enabled channel group.

## Two Notifications
  * Notification for list of all changes we get from [DifferenceItem](src/price_monitor/model/difference_item.py) dataset
  * If there are any price changes(and < 50), We provide a separate detailed notification for it.

### Supported channels
  * `gchat` : Google Chat Workspace
  * `teams` : Teams Chat Workspace

#### Example usage

- `price-monitor notify --config-file {path_to_config.json}`: send notification when changes are detected in Prices data.

In this context, `path_to_config.json` represents the relative path to the configuration file from the execution location.

Find out more about the available commands using `price-monitor --help`.
