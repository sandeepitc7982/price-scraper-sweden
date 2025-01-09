## Data Quality

* Data quality focuses on the data's fitness for use, 
Ensuring data accuracy, completeness, consistency, and reliability.
* The automation on data quality support users to get issues flagged in proactive and efficient way. 
Keeping sanity checks as low effort activities.
* We do data quality for finance options dataset which takes `finance_options_filename` as input


### Key Features:
* Change Tracking:
  * Provides historical insights on what has changed in the collected data.
  
  
* Rule Engine: 
  * Quick, digestible insights based on customizable business rules and metrics.


* Algorithm Verification: 
  * Can be utilised to verify outcomes after algorithm changes for accuracy.


* Data Quality Metrics:
  * Completeness: 
    * Ensures all expected data attributes are captured.
  * Consistency: 
    * Verifies data format and structure across sources.
  * Validity: 
    * Ensures data values are within acceptable ranges.
  * Accuracy: 
    * Verifies that data is correct and trustworthy.
  * Business Rules: 
    * Ensures data complies with defined rules and standards.

#### Example usage

- `price-monitor check-data-quality --config-file {path_to_config.json}`: to check the quality of the Finance Options data.

In this context, `path_to_config.json` represents the relative path to the configuration file from the execution location.

Find out more about the available commands using `price-monitor --help`.

#### Output
* sample_for_visual_comparison: 
  * generates sample for easy comparision
* rules_output:
  * data quality rules success percentage
* parameters:
  * generates data quality report
* insights_output:
  * all metric and success percent
* insights_failure:
  * all failures