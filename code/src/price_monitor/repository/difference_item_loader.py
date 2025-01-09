from fastavro import reader
from loguru import logger

from src.price_monitor.utils.csv_helper import load_csv_for_difference_item_loader
from src.price_monitor.utils.io import get_timestamp_from_dir_name


class DifferenceItemLoader:
    def __init__(self, output_dir, file_type, differences_filename) -> None:
        self.output_dir = output_dir
        self.file_type = file_type
        self.differences_filename = differences_filename

    def load(self, date: str, difference_item_class) -> list:
        target_dir = f"{self.output_dir}/{date}"
        output = []

        if self.file_type == "avro":
            output = self._load_avro(
                target_dir=target_dir, difference_item_class=difference_item_class
            )
        else:
            output = load_csv_for_difference_item_loader(
                differences_filename=self.differences_filename,
                target_dir=target_dir,
                difference_item_class=difference_item_class,
            )

        logger.info(f"Loaded {len(output)} items for date {date}")

        return output

    def _load_avro(self, target_dir: str, difference_item_class) -> list:
        output: list[difference_item_class] = []
        with open(f"{target_dir}/{self.differences_filename}.avro", "rb") as file:
            avro_reader = reader(file)
            for record in avro_reader:
                record.setdefault(
                    "recorded_at", get_timestamp_from_dir_name(target_dir)
                )
                output.append(difference_item_class(**record))
        if not output:
            logger.warning(
                f"No data changes found in file {target_dir}/{self.differences_filename}.avro"
            )
        return output
