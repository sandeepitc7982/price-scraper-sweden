import dataclasses
from dataclasses import dataclass

from dataclasses_avroschema import AvroModel

MISSING_LINE_OPTION_DETAILS: str = "N/A"


@dataclass(eq=True)
class LineItemOptionCode(AvroModel):
    code: str
    description: str = dataclasses.field(compare=False)
    type: str = dataclasses.field(compare=False)
    included: bool = dataclasses.field(compare=False)
    net_list_price: float = dataclasses.field(compare=False, default=0.0)
    gross_list_price: float = dataclasses.field(compare=False, default=0.0)
    predicted_category: str = dataclasses.field(compare=False, default="")

    def __eq__(self, other):
        return (
            self.code,
            self.description,
            self.type,
            self.included,
            self.net_list_price,
            self.gross_list_price,
            self.predicted_category,
        ) == (
            other.code,
            other.description,
            other.type,
            other.included,
            other.net_list_price,
            other.gross_list_price,
            other.predicted_category,
        )


def create_default_line_item_option_code(code: str):
    return LineItemOptionCode(
        **{
            "code": code,
            "description": MISSING_LINE_OPTION_DETAILS,
            "type": MISSING_LINE_OPTION_DETAILS,
            "net_list_price": 0,
            "gross_list_price": 0,
            "included": True,
        }
    )
