## Finance Scraper

The finance scraper is an additional scraper that collects financial information about car models from the same automakers.
It gathers data such as vehicle details, pricing, and financing terms (e.g., monthly payments, interest rates) across multiple regions and markets. 
The collected data helps track and analyze the latest offers available in the automotive market, enabling better decision-making for both consumers and businesses.

### BMW Finance Scraper

You can enable this scraper by adding `bmw` to your config file in the enabled finance scrapers list.

### Tesla Finance Scraper

You can enable this scraper by adding `tesla` to your config file in the enabled finance scrapers list.

### Audi Finance Scraper

You can enable this scraper by adding `audi` to your config file in the enabled finance scrapers list.

### Supported market

UK is the supported market for above-mentioned vendors by finance scraper.

### FinanceLineItem

The [FinanceLineItem](src/price_monitor/model/finance_line_item.py) dataset contains detailed financial information about vehicles, including both basic car details and the financial terms of leasing and financing offers. 
This data is used to track various market offers from different car manufacturers (vendors) across multiple regions. The dataset is saved as part of the  `finance_options_filename` output.

Schema Details

**Intended Primary Key:**

* vehicle_id
* contract_type

Disclaimer:  We initially intended to use {unique_id, contract_type} as the primary key to ensure the uniqueness of each record. 
However, we encountered scenarios, particularly with OEMs like Audi, where the same car (vehicle_id) can appear with the same contract_type (e.g., PCP) in multiple rows.  
 
As a result, this key combination does not always maintain uniqueness, and we couldn't enforce it as the primary key without compromising the completeness of the data collection.


#### FinanceLineItem dataset fields

| Field name                         | Field Description                                                                                                                                                                                                                                         | Required |
|------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| recorded_at                        | capturing the data execution/collection date & time in UTC                                                                                                                                                                                                | yes      |
| vehicle_id                         | This represents id per model by hashing of concatenation of relevant attributes                                                                                                                                                                           | yes      |
| market                             | region where service is applicable                                                                                                                                                                                                                        | yes      |
| vendor                             | the company that supplies products                                                                                                                                                                                                                        | yes      |
| series                             | group of related car models                                                                                                                                                                                                                               | yes      |
| model_range_code                   | code of vehicle offerings from particular series                                                                                                                                                                                                          | yes      |
| model_range_description            | description of vehicle offerings from particular series                                                                                                                                                                                                   | yes      |
| model_code                         | platform code for a car under particular model range                                                                                                                                                                                                      | yes      |
| model_description                  | name of the car under particular model range                                                                                                                                                                                                              | yes      |
| line_code                          | platform code of combination of characteristics/bundled options offered for a car                                                                                                                                                                         | yes      |
| line_description                   | name of the unique combination of characteristics/bundled options offered for a car                                                                                                                                                                       | yes      |
| line_option_codes                  | platform code per option available per line                                                                                                                                                                                                               | yes      |
| currency                           | market currency                                                                                                                                                                                                                                           | yes      |
| contract_type                      | specifies the structure and terms of the car finance agreement.                                                                                                                                                                                           | yes      |
| term_of_agreement                  | duration of the contract in months, typically ranges from 2 to 4 years                                                                                                                                                                                    | yes      |
| annual_mileage                     | estimated number of miles the car will be driven per year                                                                                                                                                                                                 | yes      |
| mileage_unit                       | specifies the mileage unit                                                                                                                                                                                                                                | yes      |
| deposit                            | initial upfront payment towards the financed option price of the car                                                                                                                                                                                      | yes      |
| sales_offer                        | a promotional incentive or discount applied to the car purchase price                                                                                                                                                                                     | yes      |
| total_deposit                      | the sum of the down payment and any additional upfront payments or trade-in value                                                                                                                                                                         | yes      |
| number_of_installments             | duration of the monthly payments to be made over the agreed-upon term                                                                                                                                                                                     | yes      |
| monthly_rental_nlp                 | monthly value to be paid excluding VAT                                                                                                                                                                                                                    | yes      |
| monthly_rental_glp                 | monthly value to be paid including VAT                                                                                                                                                                                                                    | yes      |
| otr (on the road)                  | otr price includes the car’s gross retail price, taxes, registration fees and any additional costs required to make the car roadworthy                                                                                                                    | yes      |
| total_payable_amount               | final amount to be paid, considering credit amount and any other charged                                                                                                                                                                                  | yes      |
| total_credit_amount                | amount borrowed by the customer to acquire the car under the finance option selected                                                                                                                                                                      | yes      |
| optional_final_payment             | a predetermined amount payable at the end of the finance agreement to own the vehicle                                                                                                                                                                     | yes      |
| option_purchase_fee                | a one-time fee charged for exercising an option within the finance agreement                                                                                                                                                                              | yes      |
| apr (Annual Percentage Rate)       | the total yearly percentage charged that includes the fixed_roi and other associated fees and charges related to the loan                                                                                                                                 | yes      |
| fixed_roi (fixed rate of interest) | the percentage charged on the borrowed amount for a year                                                                                                                                                                                                  | yes      |
| excess_mileage                     | an excess mileage charge is a penalty fee that the borrower must pay if they drive more miles than the pre-agreed mileage limit specified in annual_mileage of the PCP agreement .  It's usually paid in pence per mile(in UK) at the end of the contract | yes      |
| option_type                        | category of the option added to the car selected for financing                                                                                                                                                                                            | yes      |
| option_description                 | name of the option added to the car selected for financing                                                                                                                                                                                                | yes      |
| option_gross_list_price            | price of the option added to the car for the financing option                                                                                                                                                                                             | yes      |
| last_scraped_on                    | latest scraped date of particular record                                                                                                                                                                                                                  | no       |
| is_current                         | specifies whether we scraped a particular record from today or not                                                                                                                                                                                        | no       |

#### Example usage

- `price-monitor run-finance-scraper --config-file {path_to_config.json}`: to scrape Finance Options available for all OEMs.

In this context, `path_to_config.json` represents the relative path to the configuration file from the execution location.

Find out more about the available commands using `price-monitor --help`.