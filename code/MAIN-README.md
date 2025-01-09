# Price Monitor

This project consists of a scraper that visits the websites of various automakers and parses the latest information available
on their car models. The model information is collected over time and used to detect differences in car configurations across runs.

The project's main data point of interest is the listed car model price for each line it is available in. 
It is currently designed to be run daily and detects differences across two consecutive days.

### Price Scraper Architecture


### Scrapers

You can find Price Scraper details here - [Price Scraper](PRICE-SCRAPER-README.md)

You can find Finance Scraper details here - [Finance Scraper](FINANCE-SCRAPER-README.md)

### Comparators

You can find Price Comparator details here - [Price Comparator](PRICE-COMPARATOR-README.md)

You can find Finance Comparator details here - [Finance Comparator](FINANCE-COMPARATOR-README.md)

### Notifications

You can find Price Notifications details here - [Price Notifications](NOTIFICATIONS-README)

### Data Quality

You can find Data Quality details for Finance Options here - [Data Quality](DATA-QUALITY-README)


### Docker

You can use the `Makefile`[](Makefile) to run the scraper using docker. Run `make` to view the list of supported commands.

### Whl file

You can also use the Whl file distribution to run the scraper. Please ensure Python 3.11+ and Chrome browser is already installed on the host machine
Run `make install_from_whl` to have the `price-monitor` shell command installed on your host.

### CLI

After successfully installing the python package in your environment using one of the above methods,
you can run the CLI tool in your `shell` using the `price-monitor` command: 

![](docs/pm_shell.gif)

You can find the description of all available CLI commands [here](CLI-README.md).
For Configuration file format, refer to the Configuration file section below.

### Configuration file

The default path for [configuration file](config/local/config.json) is committed with the code and is used to tune the price monitor's behaviour in production.
> Note : To set up the config file for dev, copy the example.config.json to config/local/config.json

* Price Scraper support both relative and absolute path for directory key to save and load the data. For absolute path, make sure to pass from / onwards. ![](docs/config.png)

<details>

<summary>JSON Schema</summary>

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "environment": {
      "type": "string"
    },
    "output": {
      "type": "object",
      "properties": {
        "directory": {
          "type": "string"
        },
        "logs_directory": {
          "type": "string"
        },
        "prices_filename": {
          "type": "string"
        },
        "finance_options_filename": {
          "type": "string"
        },
        "differences_filename": {
          "type": "string"
        },
        "file_type": {
          "type": "string",
          "enum": ["csv", "avro", "dual"]
        }
      },
      "required": [
        "directory",
        "prices_filename",
        "finance_options_filename",
        "differences_filename",
        "file_type"
      ]
    },
    "scraper": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "object",
          "properties": {
            "mercedes_benz": {
              "type": "array",
              "items": [
                {
                  "type": "string",
                  "enum": ["DE","FR","AU","AT","NL","US","UK","SE"]
                }
              ]
            },
            "audi": {
              "type": "array",
              "items": [
                {
                  "type": "string",
                  "enum": ["DE","FR","AU","AT","NL","US","UK","SE"]
                }
              ]
            },
            "bmw": {
              "type": "array",
              "items": [
                {
                  "type": "string",
                  "enum": ["DE","FR","AU","AT","NL","US","UK","SE"]
                }
              ]
            },
            "tesla": {
              "type": "array",
              "items": [
                {
                  "type": "string",
                  "enum": ["DE","FR","AU","AT","NL","US","UK","SE"]
                }
              ]
            }
          }
        }
      }
    },
    "finance_scraper": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "object",
          "properties": {
            "audi": {
              "type": "array",
              "items": [
                {
                  "type": "string",
                  "enum": ["DE","FR","AU","AT","NL","US","UK","SE"]
                }
              ]
            },
            "bmw": {
              "type": "array",
              "items": [
                {
                  "type": "string",
                  "enum": ["DE","FR","AU","AT","NL","US","UK","SE"]
                }
              ]
            },
            "tesla": {
              "type": "array",
              "items": [
                {
                  "type": "string",
                  "enum": ["DE","FR","AU","AT","NL","US","UK","SE"]
                }
              ]
            }
          }
        }
      }
    },
    "notification": {
      "type": "object",
      "properties": {
        "channels": {
          "type": "object",
          "properties": {
            "gchat": {
              "type": "object",
              "properties": {
                "gchat_url": {
                  "type": "string"
                }
              },
              "required": [
                "gchat_url"
              ]
            }
          }
        },
        "urls": {
          "type": "object",
          "properties": {
            "dashboard_url": {
              "type": "string"
            }
          }
        }
      }
    },
    "feature_toggle": {
      "type": "object",
      "properties": {
        "is_type_hierarchy_enabled_MB": {
          "type": "boolean"
        }
      }
    }
  },
  "data_quality_finance": {
  },
  "required": [
    "environment",
    "output"
  ]
}
```
</details>

## Data model

The price monitor creates two datasets on every run. The output can be formatted in either `csv` or `avro` files. Defaults to `avro`.

## Operations

This section covers common questions regarding the running operations of the application.

### Environments 

* Staging
  * Our Internal Environment For Testing.
  * Each commit in main will automatically deploy to staging.
* Production
  * Used By Clients.
  * Need manual review and release process.

Each environment captures logs of the scraper runs from the standard output. Currently, these can be viewed in Google Cloud dashboards.

### Cron Job Script

The `cron_script` file is used to run the scraper and store the data into the bucket.

### Steps to Access Docker Logs from Container

- Authenticate gcloud : `gcloud auth login`
- Login to the server : `gcloud compute ssh VM-NAME --tunnel-through-iap`
  - VM-NAME
    - Production : price-monitor
    - Staging : staging-price-monitor
- List out the containers : `sudo docker ps -a` 
- Output the logs of specific container : `docker logs container_id`

### [Development Guidelines for Price Monitor](./CONTRIBUTING.md)