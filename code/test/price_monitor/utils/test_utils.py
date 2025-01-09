import pytest

from src.price_monitor.utils.utils import validate_not_blank_or_empty


def test_validate_not_blank_or_empty():
    # Test with a valid non-empty string
    validate_not_blank_or_empty("valid string", "Test Field")

    # Test with an empty string
    with pytest.raises(ValueError, match="Test Field cannot be blank or empty"):
        validate_not_blank_or_empty("", "Test Field")

    # Test with a string containing only spaces
    with pytest.raises(ValueError, match="Test Field cannot be blank or empty"):
        validate_not_blank_or_empty("   ", "Test Field")

    # Test with None
    with pytest.raises(ValueError, match="Test Field cannot be blank or empty"):
        validate_not_blank_or_empty(None, "Test Field")
