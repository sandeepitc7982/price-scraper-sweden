# `price-monitor`

Price Monitor CLI Application

**Usage**:

```console
$ price-monitor [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `check-data-quality`: Checks for data quality issues and logs...
* `notify`: Sends a notification to the configured...
* `run-compare`: Runs the price comparator and produces a...
* `run-finance-scraper`: Runs the finance scraper and saves the...
* `run-scraper`: Runs the price scraper and saves the...

## `price-monitor run-scraper`

Runs the price scraper and saves the scraped data to a local directory in the specified file format.

**Usage**:

```console
$ price-monitor run-scraper [OPTIONS]
```

**Options**:

* `--config-file PATH`: File path to a json config  [required]
* `--scraper [bmw|tesla|audi|mercedes_benz]`: Run one scraper from the supported scrapers
* `--market [DE|FR|AU|AT|NL|US|UK|SE]`: Scrape one market from the supported markets
* `--output [csv|avro|dual]`: Set the output file format
* `--directory TEXT`: Set the output file directory
* `--help`: Show this message and exit.

## `price-monitor run-finance-scraper`

Runs the finance scraper and saves the scraped data to a local directory in the specified file format.

**Usage**:

```console
$ price-monitor run-finance-scraper [OPTIONS]
```

**Options**:

* `--config-file PATH`: File path to a json config  [required]
* `--scraper [bmw|tesla|audi|mercedes_benz]`: Run one scraper from the supported scrapers
* `--market [DE|FR|AU|AT|NL|US|UK|SE]`: Scrape one market from the supported markets
* `--output [csv|avro|dual]`: Set the output file format
* `--directory TEXT`: Set the output file directory
* `--help`: Show this message and exit.

## `price-monitor run-compare`

Runs the price comparator and produces a changelog of differences between today and yesterday's data.

**Usage**:

```console
$ price-monitor run-compare [OPTIONS]
```

**Options**:

* `--config-file PATH`: File path to a json config  [required]
* `--output [csv|avro|dual]`: Set the output file format
* `--directory TEXT`: Set the output file directory
* `--help`: Show this message and exit.

## `price-monitor run-finance-compare`

Runs the finance comparator and produces a changelog of differences between today and yesterday's data.

**Usage**:

```console
$ price-monitor run-finance-compare [OPTIONS]
```

**Options**:

* `--config-file PATH`: File path to a json config  [required]
* `--output [csv|avro|dual]`: Set the output file format
* `--directory TEXT`: Set the output file directory
* `--help`: Show this message and exit.

## `price-monitor notify`

Sends a notification to the configured destinations if a changelog is detected for the current day.

**Usage**:

```console
$ price-monitor notify [OPTIONS]
```

**Options**:

* `--config-file PATH`: File path to a json config  [required]
* `--directory TEXT`: Set the output file directory
* `--help`: Show this message and exit.

## `price-monitor check-data-quality`

Checks for data quality issues and logs its findings.

**Usage**:

```console
$ price-monitor check-data-quality [OPTIONS]
```

**Options**:

* `--config-file PATH`: File path to a json config  [required]
* `--directory TEXT`: Set the output file directory
* `--help`: Show this message and exit.


### Configuration file

The default path for [configuration file](../../config/local/config.json) is committed with the code and is used to tune the price monitor's behaviour in production.
> Note : To set up the config file for dev, copy the example.config.json to config/local/config.json

* Price Scraper support both relative and absolute path for directory key to save and load the data. For absolute path, make sure to pass from / onwards. ![](docs/images/config.png)

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