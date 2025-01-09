## Price Comparator
This comparator captures the list of changes in car models between 
two consecutive runs (currently two days)

### Supported vendors

BMW, Audi, Mercedes Benz, Tesla

### Supported markets

BMW [supported markets](src/price_monitor/scraper/bmw/constants.py)

Audi [supported markets](src/price_monitor/scraper/audi/constants.py)

Mercedes Benz [supported markets](src/price_monitor/scraper/mercedes_benz/constants.py)

Tesla [supported markets](src/price_monitor/scraper/tesla/constants.py)

## Change Detection

According to these categories, price comparator detects changes in car models from prices data:

- New car line added
- Car line removed
- Price change for existing car line
- New option added to existing car line
- Option removed from existing car line

## These are different comparators we have under Price Comparator

### DifferenceItem

The [DifferenceItem](../../src/price_monitor/model/difference_item.py) dataset consists of a list of detected changes between two 
consecutive runs (currently two days) by comparing each one's [LineItem](../../src/price_monitor/model/line_item.py) dataset.
This dataset is saved in the `changelog_filename` output.

Schema Details

**Primary Key:**

* market
* vendor
* series
* model_range_code
* model_code
* line_code

| Field name              | Field Description                                                                   | Required |
|-------------------------|-------------------------------------------------------------------------------------|----------|
| recorded_at             | capturing the data execution/collection date & time in UTC                          | yes      |
| market                  | region where service is applicable                                                  | yes      |
| vendor                  | the company that supplies products                                                  | yes      |
| series                  | group of related car models                                                         | yes      |
| model_range_code        | code of vehicle offerings from particular series                                    | yes      |
| model_range_description | description of vehicle offerings from particular series                             | yes      |
| model_code              | platform code for a car under particular model range                                | yes      |
| model_description       | name of the car under particular model range                                        | yes      |
| line_code               | platform code of combination of characteristics/bundled options offered for a car   | yes      |
| line_description        | name of the unique combination of characteristics/bundled options offered for a car | yes      |
| old_value               | value from previous date date                                                       | no       |
| new_value               | changed new value scraped from current date data                                    | no       |
| reason                  | reason for change (specifying category changed)                                     | yes      |

### PriceDifferenceItem

The [PriceDifferenceItem](../../src/price_monitor/model/price_difference_item.py) dataset consists of a list of detected price changes between two
consecutive runs (currently two days) by filtering price changes from [DifferenceItem](../../src/price_monitor/model/difference_item.py) dataset.
This dataset is saved in the `price_changelog_filename` output.

Schema Details

**Primary Key:**

* market
* vendor
* series
* model_range_code
* model_code
* line_code

| Field name              | Field Description                                                                   | Required |
|-------------------------|-------------------------------------------------------------------------------------|----------|
| recorded_at             | capturing the data execution/collection date & time in UTC                          | yes      |
| market                  | region where service is applicable                                                  | yes      |
| vendor                  | the company that supplies products                                                  | yes      |
| series                  | group of related car models                                                         | yes      |
| model_range_code        | code of vehicle offerings from particular series                                    | yes      |
| model_range_description | description of vehicle offerings from particular series                             | yes      |
| model_code              | platform code for a car under particular model range                                | yes      |
| model_description       | name of the car under particular model range                                        | yes      |
| line_code               | platform code of combination of characteristics/bundled options offered for a car   | yes      |
| line_description        | name of the unique combination of characteristics/bundled options offered for a car | yes      |
| old_price               | price of car from previous date date                                                | yes      |
| new_price               | changed new price of car scraped from current date data                             | yes      |
| currency                | market currency                                                                     | yes      |
| perc_change             | Calculates the percentage of change considering new and old price value             | yes      |
| model_price_change      | calculates price change                                                             | yes      |
| reason                  | reason for change (specifying category changed)                                     | yes      |
| option_code             | code of option changed                                                              | yes      |
| option_gross_list_price | changed option glp                                                                  | yes      |
| option_net_list_price   | changed option nlp                                                                  | yes      |


### OptionPriceDifferenceItem

The [OptionPriceDifferenceItem](../../src/price_monitor/model/option_price_difference_item.py) dataset consists of a list of detected option price changes between two
consecutive runs (currently two days) by filtering option price changes from [DifferenceItem](../../src/price_monitor/model/difference_item.py) dataset.
This dataset is saved in the `option_price_changelog_filename` output.

Schema Details

**Primary Key:**

* market
* vendor

| Field name              | Field Description                                                              | Required |
|-------------------------|--------------------------------------------------------------------------------|----------|
| recorded_at             | capturing the data execution/collection date & time in UTC                     | yes      |
| market                  | region where service is applicable                                             | yes      |
| vendor                  | the company that supplies products                                             | yes      |
| model_range_description | description of vehicle offerings from particular series                        | yes      |
| option_description      | name of the option changed                                                     | yes      |
| option_old_price        | option price value from previous date date                                     | yes      |
| option_new_price        | changed new price of option scraped from current date data                     | yes      |
| currency                | market currency                                                                | yes      |
| perc_change             | Calculates the percentage of change considering new and old option price value | yes      |
| option_price_change     | calculates option price change                                                 | yes      |
| reason                  | reason for change (specifying category changed)                                | yes      |
| option_code             | code of option changed                                                         | yes      |


#### Example usage

- `price-monitor run-compare --config-file {path_to_config.json}`: to find differences between today's and yesterday's Prices data.

In this context, `path_to_config.json` represents the relative path to the configuration file from the execution location.

Find out more about the available commands using `price-monitor --help`.

> Note : From 4th May 2023 onwards, Comparison for price change column has changed from gross list price to net list price for production.

