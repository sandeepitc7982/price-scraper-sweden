import re


def remove_new_line_characters(input: str) -> str:
    return re.sub(" *\\n *", " ", input)


def validate_not_blank_or_empty(value: str, field_name: str):
    if not value or len(value.strip()) == 0:
        raise ValueError(f"{field_name} cannot be blank or empty")
