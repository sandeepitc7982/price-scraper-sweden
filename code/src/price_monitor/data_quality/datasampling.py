import random
from typing import List

import pandas as pd
from loguru import logger


class ScraperVerificationSample:
    def __init__(self, df: pd.DataFrame, config):
        self.df = df
        self.config = config
        self.additional_columns = self.get_additional_columns()
        self.sampled_cars = pd.DataFrame()
        self.current_index = 0  # Track the current index in the additional_columns list

    def get_additional_columns(self) -> List[str]:
        """
        Returns a list of additional columns to be verified, excluding the navigation columns and excluded columns.
        """
        navigation_columns = self.config["data_quality_finance"][
            "data_sampling_config"
        ]["navigation_columns"]
        excluded_columns = self.config["data_quality_finance"]["data_sampling_config"][
            "exclude_columns_sample"
        ]
        all_columns = self.df.columns.tolist()
        additional_columns = [
            col
            for col in all_columns
            if col not in navigation_columns and col not in excluded_columns
        ]
        return additional_columns

    def select_columns_for_car(self, car_index: int) -> List[str]:
        columns_per_car = self.config["data_quality_finance"]["data_sampling_config"][
            "columns_per_car"
        ]
        """
        Selects columns for verification in order of their presence in the DataFrame.
        Iterates through columns in a circular manner, ensuring no column is left out.
        """
        try:
            num_columns = len(self.additional_columns)
            selected_columns = []

            # Start selecting columns, and continue from the current index
            for _ in range(columns_per_car):
                # Select the column at the current index
                selected_columns.append(self.additional_columns[self.current_index])

                # Move to the next column
                self.current_index += 1

                # If the current index exceeds the number of available columns, wrap around to 0
                if self.current_index >= num_columns:
                    self.current_index = 0
            logger.debug(
                f"Selected columns for car at index {car_index}: {selected_columns}"
            )
            return selected_columns

        except Exception as e:
            logger.error(f"Error selecting columns for car at index {car_index}: {e}")
            return []

    def generate_sample(self) -> pd.DataFrame:
        columns_per_car = self.config["data_quality_finance"]["data_sampling_config"][
            "columns_per_car"
        ]
        navigation_columns = self.config["data_quality_finance"][
            "data_sampling_config"
        ]["navigation_columns"]
        min_sample_required = self.config["data_quality_finance"][
            "data_sampling_config"
        ]["number_of_samples_for_verification"]

        try:
            # Filter the data based on vendor-specific conditions
            vendor = self.df["vendor"].unique()[
                0
            ]  # Assuming all rows have the same vendor
            filtered_df = self.filter_data_by_vendor(vendor)
            self.df = filtered_df
            num_additional_columns = len(self.additional_columns)
            # Calculate the number of cars needed to cover all columns
            cars_needed_to_cover_columns = (
                num_additional_columns + columns_per_car - 1
            ) // columns_per_car
            # Ensure that we meet the minimum sample requirement
            num_cars = max(min_sample_required, cars_needed_to_cover_columns)
            # If there's any possibility of missing columns, add one more car
            if num_cars * columns_per_car < num_additional_columns:
                num_cars += 1

            sample_length = len(self.df)
            # Ensure we don't exceed the available cars in the data
            logger.debug(
                f"Total Cars: {num_cars}, Additional Columns: {num_additional_columns}, "
                f"Number of Cars Needed: {cars_needed_to_cover_columns}"
            )

            sampled_data = []  # List to collect sampled data

            # Generate sample
            for car_index in random.sample(range(sample_length), num_cars):
                selected_columns = self.select_columns_for_car(car_index)
                all_columns = navigation_columns + selected_columns

                # Ensure all selected columns are included in the DataFrame
                car_data = self.df.iloc[car_index]
                missing_columns = [
                    col for col in all_columns if col not in self.df.columns
                ]

                if missing_columns:
                    logger.warning(
                        f"Columns {missing_columns} not found in DataFrame and will be included as empty."
                    )

                # Create a new DataFrame with the required format
                formatted_data = pd.DataFrame(
                    {
                        "vendor": [car_data["vendor"]],
                        "market": [car_data["market"]],
                        **{
                            col: [car_data.get(col, None)] for col in navigation_columns
                        },
                        **{col: [car_data.get(col, None)] for col in selected_columns},
                    }
                )

                # Append formatted data to the list
                sampled_data.append(formatted_data)

            self.sampled_cars = pd.concat(
                sampled_data, ignore_index=True
            )  # Use pd.concat to combine data
            logger.debug(f"Sampled results: {self.sampled_cars}")
            return self.sampled_cars

        except Exception as e:
            logger.error(f"Error generating sample: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error

    def filter_data_by_vendor(self, vendor: str) -> pd.DataFrame:
        """
        Filters the data based on vendor-specific column and value conditions
        provided in the config.
        """
        try:
            # Get the filtering conditions for the vendor
            filter_conditions = self.config["data_quality_finance"][
                "data_sampling_config"
            ]["vendor_filter_config"][vendor]
            # If no filter conditions are provided for the vendor, return the full dataset
            if not filter_conditions:
                return self.df

            # Filter the DataFrame based on the vendor-specific conditions
            filtered_df = self.df
            for column, text_value in filter_conditions.items():
                # Ensure that the column exists in the DataFrame
                if column in self.df.columns:
                    # Filter rows where the column contains the text value (case insensitive)
                    filtered_df = filtered_df[
                        filtered_df[column].str.contains(
                            text_value, case=False, na=False
                        )
                    ]

            # Return the filtered DataFrame
            return filtered_df

        except Exception as e:
            logger.error(f"Error filtering data for vendor {vendor}: {e}")
            return self.df  # Return full data if any error occurs
