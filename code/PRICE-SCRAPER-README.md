## Price Scraper

Each supported automaker has their own scraper that connects to their public website and parses information on their car
models. Since the scrapers are pulling information from undocumented public data sources, it is a best-effort
process that can vary in quality and granularity across automakers.

### BMW Scraper

You can enable this scraper by adding `bmw` to your config file in the enabled scrapers list.
Check the [supported markets](src/price_monitor/scraper/bmw/constants.py) constant for a list of supported markets by this scraper.

### Tesla Scraper

You can enable this scraper by adding `tesla` to your config file in the enabled scrapers list.
Check the [supported markets](src/price_monitor/scraper/tesla/constants.py) constant for a list of supported markets by this scraper.

### Audi Scraper

You can enable this scraper by adding `audi` to your config file in the enabled scrapers list.
Check the [supported markets](src/price_monitor/scraper/audi/constants.py) constant for a list of supported markets by this scraper.

### Mercedes Benz Scraper

You can enable this scraper by adding `mercedes` to your config file in the enabled scrapers list.
Check the [supported markets](src/price_monitor/scraper/mercedes_benz/constants.py) constant for a list of supported markets by this scraper.

### LineItem

The [LineItem](src/price_monitor/model/line_item.py) dataset consists of a list of vehicle models for every vendor and market.
Each line item has an associated price and a list of included options. This dataset is saved in the `prices_filename` output.

Schema Details

**Primary Keys:**

* market
* vendor
* series
* model_range_code
* model_code
* line_code

#### LineItem dataset fields

| Field name              | Field Description                                                                                                                       | Required |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|----------|
| recorded_at             | capturing the data execution/collection date & time in UTC                                                                              | yes      |
| market                  | region where service is applicable                                                                                                      | yes      |
| vendor                  | the company that supplies products                                                                                                      | yes      |
| series                  | group of related car models                                                                                                             | yes      |
| model_range_code        | code of vehicle offerings from particular series                                                                                        | yes      |
| model_range_description | description of vehicle offerings from particular series                                                                                 | yes      |
| model_code              | platform code for a car under particular model range                                                                                    | yes      |
| model_description       | name of the car under particular model range                                                                                            | yes      |
| line_code               | platform code of combination of characteristics/bundled options offered for a car                                                       | yes      |
| line_description        | name of the unique combination of characteristics/bundled options offered for a car                                                     | yes      |
| line_option_codes       | platform code per option available per line                                                                                             | yes      |
| currency                | market currency                                                                                                                         | yes      |
| net_list_price          | car’s retail price excluding VAT                                                                                                        | yes      |
| gross_list_price        | Car’s retail price including VAT                                                                                                        | yes      |
| engine_performance_kw   | engine performance in kilowatts (kW)                                                                                                    | yes      |
| engine_performance_hp   | engine performance in horsepower (hp)                                                                                                   | yes      |
| one_the_road_price      | OTR price includes the car’s gross retail price, taxes, registration fees and any additional costs required to make the car roadworthy. | no       |
| last_scraped_on         | latest scraped date of particular record                                                                                                | no       |
| is_current              | specifies whether we scraped a particular record from today or not                                                                      | no       |


#### Example usage
 
- `price-monitor run-scraper --config-file {path_to_config.json}`: to scrape the Prices data for all OEMs.

In this context, `path_to_config.json` represents the relative path to the configuration file from the execution location.

Find out more about the available commands using `price-monitor --help`.