## Finance Comparator
This comparator captures the list of finance changes in car models between 
two consecutive runs (currently two days)

### Supported vendors

BMW, Audi, Tesla

### Supported markets

UK is the supported market for above-mentioned vendors by finance comparator.

## Change Detection

According to these categories, finance comparator detects changes in car models from finance options data:

- New PCP Finance Option Added
- PCP Finance Removed
- PCP Finance Option Changes( monthly_rental, sales_offer, OTR, APR, ROI, Optional Purchase Payments )

## This is the comparator we have under finance Comparator

### DifferenceFinanceItem

The [DifferenceFinanceItem](src/price_monitor/finance_comparer/difference_finance_item.py) dataset consists of a list of detected finance changes between two
consecutive runs (currently two days) by filtering finance changes from [FinanceLineItem](src/price_monitor/model/finance_line_item.py)  dataset.
This dataset is saved in the `finance_options_changelog_filename` output.

Schema Details

**Intended Primary Key:**

* vehicle_id
* contract_type

| Field name              | Field Description                                                                   | Required |
|-------------------------|-------------------------------------------------------------------------------------|----------|
| recorded_at             | capturing the data execution/collection date & time in UTC                          | yes      |
| vehicle_id              | This represents id per model by hashing of concatenation of relevant attributes     | yes      |
| market                  | region where service is applicable                                                  | yes      |
| vendor                  | the company that supplies products                                                  | yes      |
| series                  | group of related car models                                                         | yes      |
| model_range_code        | code of vehicle offerings from particular series                                    | yes      |
| model_range_description | description of vehicle offerings from particular series                             | yes      |
| model_code              | platform code for a car under particular model range                                | yes      |
| model_description       | name of the car under particular model range                                        | yes      |
| line_code               | platform code of combination of characteristics/bundled options offered for a car   | yes      |
| line_description        | name of the unique combination of characteristics/bundled options offered for a car | yes      |
| contract_type           | specifies the structure and terms of the car finance agreement.                     | yes      |
| old_value               | value from previous date date                                                       | no       |
| new_value               | changed new value scraped from current date data                                    | no       |
| reason                  | reason for change (specifying category changed)                                     | yes      |


#### Example usage

- `price-monitor run-finance-compare --config-file {path_to_config.json}`: to find differences between today's and yesterday's Finance Options data.

In this context, `path_to_config.json` represents the relative path to the configuration file from the execution location.

Find out more about the available commands using `price-monitor --help`.
