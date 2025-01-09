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
