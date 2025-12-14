"""
Numeric filter implementations.
"""

from typing import Any

from .base import Filter, FilterOperator


class NumericFilter(Filter):
  """Filter for numeric comparisons."""

  def __init__(self, field: str, operator: FilterOperator, value: Any, case_sensitive: bool = False):
    super().__init__(field, operator, value, case_sensitive)
    # Convert value to numeric type
    self.numeric_value = self._parse_numeric_value(value)

  def _parse_numeric_value(self, value: Any) -> int | float | tuple:
    """Parse value to numeric type."""
    if self.operator == FilterOperator.BETWEEN:
      # Handle range values like "5-10" or "5,10"
      if isinstance(value, str):
        if "-" in value:
          parts = value.split("-")
        elif "," in value:
          parts = value.split(",")
        else:
          raise ValueError(f"Invalid range format: {value}")

        if len(parts) != 2:
          raise ValueError(f"Range must have exactly 2 values: {value}")

        return (self._to_number(parts[0]), self._to_number(parts[1]))
      elif isinstance(value, list | tuple) and len(value) == 2:
        return (self._to_number(value[0]), self._to_number(value[1]))
      else:
        raise ValueError(f"Invalid range value: {value}")
    else:
      return self._to_number(value)

  def _to_number(self, value: Any) -> int | float:
    """Convert a single value to number."""
    if isinstance(value, int | float):
      return value

    try:
      # Try int first
      if isinstance(value, str) and "." not in value:
        return int(value)
      else:
        return float(value)
    except (ValueError, TypeError):
      raise ValueError(f"Cannot convert to number: {value}")

  def matches(self, model_data: dict[str, Any]) -> bool:
    """Check if the model data matches this numeric filter."""
    field_value = self.get_field_value(model_data)

    # Handle None/missing values
    if field_value is None:
      if self.operator == FilterOperator.NOT_EXISTS:
        return True
      elif self.operator == FilterOperator.EXISTS:
        return False
      else:
        return False  # None doesn't match numeric comparisons

    # Convert field value to number
    try:
      numeric_field_value = self._to_number(field_value)
    except ValueError:
      return False  # Non-numeric values don't match

    # Apply operator
    if self.operator in (FilterOperator.EQ, FilterOperator.EQUALS):
      return numeric_field_value == self.numeric_value

    elif self.operator in (FilterOperator.NE, FilterOperator.NOT_EQUALS):
      return numeric_field_value != self.numeric_value

    elif self.operator == FilterOperator.LT:
      return numeric_field_value < self.numeric_value

    elif self.operator == FilterOperator.LE:
      return numeric_field_value <= self.numeric_value

    elif self.operator == FilterOperator.GT:
      return numeric_field_value > self.numeric_value

    elif self.operator == FilterOperator.GE:
      return numeric_field_value >= self.numeric_value

    elif self.operator == FilterOperator.BETWEEN:
      min_val, max_val = self.numeric_value
      return min_val <= numeric_field_value <= max_val

    elif self.operator == FilterOperator.IN:
      # Handle list of numbers
      if isinstance(self.value, str):
        values = [self._to_number(v.strip()) for v in self.value.split(",")]
      else:
        values = [self._to_number(v) for v in self.value]

      return numeric_field_value in values

    elif self.operator == FilterOperator.NOT_IN:
      # Handle list of numbers
      if isinstance(self.value, str):
        values = [self._to_number(v.strip()) for v in self.value.split(",")]
      else:
        values = [self._to_number(v) for v in self.value]

      return numeric_field_value not in values

    elif self.operator == FilterOperator.EXISTS:
      return True  # We already checked for None above

    elif self.operator == FilterOperator.NOT_EXISTS:
      return False  # We already checked for None above

    else:
      raise ValueError(f"Unsupported numeric operator: {self.operator}")


# fin
