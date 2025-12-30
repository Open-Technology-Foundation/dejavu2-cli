"""
Tests for NumericFilter.
"""

import pytest

from filters.base import FilterOperator
from filters.numeric_filters import NumericFilter


class TestNumericFilterComparisons:
  """Tests for basic numeric comparison operators."""

  def test_equals_int(self, sample_model_data: dict) -> None:
    """Test == operator with integer."""
    filter_obj = NumericFilter("available", FilterOperator.EQ, 9)
    assert filter_obj.matches(sample_model_data) is True

  def test_equals_from_string(self, sample_model_data: dict) -> None:
    """Test == operator with string value."""
    filter_obj = NumericFilter("available", FilterOperator.EQ, "9")
    assert filter_obj.matches(sample_model_data) is True

  def test_equals_no_match(self, sample_model_data: dict) -> None:
    """Test == operator with non-matching value."""
    filter_obj = NumericFilter("available", FilterOperator.EQ, 5)
    assert filter_obj.matches(sample_model_data) is False

  def test_not_equals_match(self, sample_model_data: dict) -> None:
    """Test != operator match."""
    filter_obj = NumericFilter("available", FilterOperator.NE, 5)
    assert filter_obj.matches(sample_model_data) is True

  def test_not_equals_no_match(self, sample_model_data: dict) -> None:
    """Test != operator no match."""
    filter_obj = NumericFilter("available", FilterOperator.NE, 9)
    assert filter_obj.matches(sample_model_data) is False

  def test_less_than_match(self, sample_model_data: dict) -> None:
    """Test < operator match."""
    filter_obj = NumericFilter("available", FilterOperator.LT, 10)
    assert filter_obj.matches(sample_model_data) is True

  def test_less_than_no_match(self, sample_model_data: dict) -> None:
    """Test < operator no match."""
    filter_obj = NumericFilter("available", FilterOperator.LT, 9)
    assert filter_obj.matches(sample_model_data) is False

  def test_less_than_or_equal_match(self, sample_model_data: dict) -> None:
    """Test <= operator match."""
    filter_obj = NumericFilter("available", FilterOperator.LE, 9)
    assert filter_obj.matches(sample_model_data) is True

  def test_less_than_or_equal_no_match(self, sample_model_data: dict) -> None:
    """Test <= operator no match."""
    filter_obj = NumericFilter("available", FilterOperator.LE, 8)
    assert filter_obj.matches(sample_model_data) is False

  def test_greater_than_match(self, sample_model_data: dict) -> None:
    """Test > operator match."""
    filter_obj = NumericFilter("available", FilterOperator.GT, 8)
    assert filter_obj.matches(sample_model_data) is True

  def test_greater_than_no_match(self, sample_model_data: dict) -> None:
    """Test > operator no match."""
    filter_obj = NumericFilter("available", FilterOperator.GT, 9)
    assert filter_obj.matches(sample_model_data) is False

  def test_greater_than_or_equal_match(self, sample_model_data: dict) -> None:
    """Test >= operator match."""
    filter_obj = NumericFilter("available", FilterOperator.GE, 9)
    assert filter_obj.matches(sample_model_data) is True

  def test_greater_than_or_equal_no_match(self, sample_model_data: dict) -> None:
    """Test >= operator no match."""
    filter_obj = NumericFilter("available", FilterOperator.GE, 10)
    assert filter_obj.matches(sample_model_data) is False


class TestNumericFilterBetween:
  """Tests for between operator."""

  def test_between_match_hyphen(self, sample_model_data: dict) -> None:
    """Test between with hyphen separator."""
    filter_obj = NumericFilter("available", FilterOperator.BETWEEN, "5-10")
    assert filter_obj.matches(sample_model_data) is True

  def test_between_match_comma(self, sample_model_data: dict) -> None:
    """Test between with comma separator."""
    filter_obj = NumericFilter("available", FilterOperator.BETWEEN, "5,10")
    assert filter_obj.matches(sample_model_data) is True

  def test_between_at_boundary(self, sample_model_data: dict) -> None:
    """Test between at exact boundaries."""
    filter_obj = NumericFilter("available", FilterOperator.BETWEEN, "9-9")
    assert filter_obj.matches(sample_model_data) is True

  def test_between_no_match(self, sample_model_data: dict) -> None:
    """Test between with out-of-range value."""
    filter_obj = NumericFilter("available", FilterOperator.BETWEEN, "1-5")
    assert filter_obj.matches(sample_model_data) is False

  def test_between_tuple_input(self, sample_model_data: dict) -> None:
    """Test between with tuple input."""
    filter_obj = NumericFilter("available", FilterOperator.BETWEEN, (5, 10))
    assert filter_obj.matches(sample_model_data) is True

  def test_between_list_input(self, sample_model_data: dict) -> None:
    """Test between with list input."""
    filter_obj = NumericFilter("available", FilterOperator.BETWEEN, [5, 10])
    assert filter_obj.matches(sample_model_data) is True

  def test_between_invalid_format(self) -> None:
    """Test between with invalid format raises error."""
    with pytest.raises(ValueError, match="Invalid range"):
      NumericFilter("available", FilterOperator.BETWEEN, "invalid")

  def test_between_wrong_parts_count(self) -> None:
    """Test between with wrong number of parts."""
    with pytest.raises(ValueError, match="exactly 2 values"):
      NumericFilter("available", FilterOperator.BETWEEN, "1-2-3")


class TestNumericFilterInNotIn:
  """Tests for in/not_in operators.

  Note: NumericFilter doesn't properly support IN/NOT_IN at construction time
  because _parse_numeric_value tries to convert the comma-separated string to
  a number. In practice, FilterChain routes these to StringFilter.
  """

  @pytest.mark.xfail(reason="NumericFilter doesn't handle IN value parsing at construction")
  def test_in_match(self, sample_model_data: dict) -> None:
    """Test in operator with matching value."""
    filter_obj = NumericFilter("available", FilterOperator.IN, "7,8,9")
    assert filter_obj.matches(sample_model_data) is True

  @pytest.mark.xfail(reason="NumericFilter doesn't handle IN value parsing at construction")
  def test_in_no_match(self, sample_model_data: dict) -> None:
    """Test in operator with non-matching value."""
    filter_obj = NumericFilter("available", FilterOperator.IN, "1,2,3")
    assert filter_obj.matches(sample_model_data) is False

  @pytest.mark.xfail(reason="NumericFilter doesn't handle list input for IN at construction")
  def test_in_list_input(self, sample_model_data: dict) -> None:
    """Test in operator with list input."""
    filter_obj = NumericFilter("available", FilterOperator.IN, [7, 8, 9])
    assert filter_obj.matches(sample_model_data) is True

  @pytest.mark.xfail(reason="NumericFilter doesn't handle NOT_IN value parsing at construction")
  def test_not_in_match(self, sample_model_data: dict) -> None:
    """Test not_in with non-matching values."""
    filter_obj = NumericFilter("available", FilterOperator.NOT_IN, "1,2,3")
    assert filter_obj.matches(sample_model_data) is True

  @pytest.mark.xfail(reason="NumericFilter doesn't handle NOT_IN value parsing at construction")
  def test_not_in_no_match(self, sample_model_data: dict) -> None:
    """Test not_in with matching value."""
    filter_obj = NumericFilter("available", FilterOperator.NOT_IN, "7,8,9")
    assert filter_obj.matches(sample_model_data) is False


class TestNumericFilterExists:
  """Tests for exists/not_exists operators.

  Note: NumericFilter doesn't properly support EXISTS/NOT_EXISTS at construction
  time because _parse_numeric_value tries to convert empty string to a number.
  In practice, FilterChain routes these to StringFilter.
  """

  @pytest.mark.xfail(reason="NumericFilter doesn't handle empty value for EXISTS")
  def test_exists_true(self, sample_model_data: dict) -> None:
    """Test exists on existing numeric field."""
    filter_obj = NumericFilter("available", FilterOperator.EXISTS, "")
    assert filter_obj.matches(sample_model_data) is True

  @pytest.mark.xfail(reason="NumericFilter doesn't handle empty value for EXISTS")
  def test_exists_false(self, sample_model_data: dict) -> None:
    """Test exists on missing field."""
    filter_obj = NumericFilter("nonexistent", FilterOperator.EXISTS, "")
    assert filter_obj.matches(sample_model_data) is False

  @pytest.mark.xfail(reason="NumericFilter doesn't handle empty value for NOT_EXISTS")
  def test_not_exists_true(self, sample_model_data: dict) -> None:
    """Test not_exists on missing field."""
    filter_obj = NumericFilter("nonexistent", FilterOperator.NOT_EXISTS, "")
    assert filter_obj.matches(sample_model_data) is True

  @pytest.mark.xfail(reason="NumericFilter doesn't handle empty value for NOT_EXISTS")
  def test_not_exists_false(self, sample_model_data: dict) -> None:
    """Test not_exists on existing field."""
    filter_obj = NumericFilter("available", FilterOperator.NOT_EXISTS, "")
    assert filter_obj.matches(sample_model_data) is False


class TestNumericFilterNestedFields:
  """Tests for nested field access with numeric values."""

  def test_nested_numeric_field(self, sample_model_data: dict) -> None:
    """Test accessing nested numeric fields."""
    filter_obj = NumericFilter("nested.number", FilterOperator.EQ, 42)
    assert filter_obj.matches(sample_model_data) is True


class TestNumericFilterEdgeCases:
  """Tests for edge cases and type handling."""

  def test_none_value_comparison(self) -> None:
    """Test that None values don't match numeric comparisons."""
    data = {"field": None}
    filter_obj = NumericFilter("field", FilterOperator.EQ, 0)
    assert filter_obj.matches(data) is False

  def test_missing_field_comparison(self) -> None:
    """Test that missing fields don't match numeric comparisons."""
    data = {}
    filter_obj = NumericFilter("field", FilterOperator.EQ, 0)
    assert filter_obj.matches(data) is False

  def test_non_numeric_field_value(self) -> None:
    """Test that non-numeric string values don't match."""
    data = {"field": "not a number"}
    filter_obj = NumericFilter("field", FilterOperator.EQ, 0)
    assert filter_obj.matches(data) is False

  def test_float_comparison(self) -> None:
    """Test float comparison."""
    data = {"field": 3.14}
    filter_obj = NumericFilter("field", FilterOperator.GT, 3.0)
    assert filter_obj.matches(data) is True

  def test_float_from_string(self) -> None:
    """Test float parsed from string."""
    data = {"field": 3.14}
    filter_obj = NumericFilter("field", FilterOperator.EQ, "3.14")
    assert filter_obj.matches(data) is True

  def test_large_context_window(self, sample_model_data: dict) -> None:
    """Test comparison with large numbers."""
    filter_obj = NumericFilter("context_window", FilterOperator.GE, 100000)
    assert filter_obj.matches(sample_model_data) is True

  def test_invalid_value_raises_error(self) -> None:
    """Test that invalid value raises ValueError."""
    with pytest.raises(ValueError, match="Cannot convert"):
      NumericFilter("field", FilterOperator.EQ, "not a number")


# fin
