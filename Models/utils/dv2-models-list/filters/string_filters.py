"""
String-based filter implementations.
"""

import re
from functools import lru_cache
from typing import Any

from .base import Filter, FilterOperator

# Regex safety constants
MAX_REGEX_LENGTH = 500
# Patterns that can cause catastrophic backtracking (ReDoS)
DANGEROUS_REGEX_PATTERNS = [
  r'\(\[?[^)]*[+*]\)?[+*]',  # Nested quantifiers like (a+)+ or ([a-z]+)*
  r'\([^)]*\|[^)]*\)[+*]',   # Alternation with quantifier like (a|b)+
]


class RegexValidationError(ValueError):
  """Raised when a regex pattern fails validation."""
  pass


def validate_regex_pattern(pattern: str) -> None:
  """
  Validate that a regex pattern is safe to compile and execute.

  Args:
    pattern: The regex pattern to validate

  Raises:
    RegexValidationError: If the pattern is unsafe or too long
  """
  if len(pattern) > MAX_REGEX_LENGTH:
    raise RegexValidationError(
      f"Regex pattern too long ({len(pattern)} chars, max {MAX_REGEX_LENGTH})"
    )

  for dangerous in DANGEROUS_REGEX_PATTERNS:
    if re.search(dangerous, pattern):
      raise RegexValidationError(
        f"Regex pattern contains potentially dangerous construct: {pattern[:50]}..."
        if len(pattern) > 50 else f"Regex pattern contains potentially dangerous construct: {pattern}"
      )

  # Try to compile the pattern to catch syntax errors early
  try:
    re.compile(pattern)
  except re.error as e:
    raise RegexValidationError(f"Invalid regex pattern: {e}") from e


@lru_cache(maxsize=256)
def _compile_regex(pattern: str, flags: int) -> re.Pattern:
  """
  Compile and cache a regex pattern.

  Args:
    pattern: The regex pattern to compile
    flags: Regex flags (e.g., re.IGNORECASE)

  Returns:
    Compiled regex pattern
  """
  return re.compile(pattern, flags)


class StringFilter(Filter):
  """Filter for string-based comparisons."""

  def __init__(self, field: str, operator: FilterOperator, value: Any, case_sensitive: bool = False):
    super().__init__(field, operator, value, case_sensitive)

    # Pre-compute values for performance
    self._compare_value = str(value) if case_sensitive else str(value).lower()

    # Pre-compile and validate regex patterns
    self._compiled_regex: re.Pattern | None = None
    if operator == FilterOperator.REGEX:
      validate_regex_pattern(str(value))
      flags = 0 if case_sensitive else re.IGNORECASE
      self._compiled_regex = _compile_regex(str(value), flags)

  def matches(self, model_data: dict[str, Any]) -> bool:
    """Check if the model data matches this string filter."""
    field_value = self.get_field_value(model_data)

    # Handle None/missing values
    if field_value is None:
      if self.operator == FilterOperator.NOT_EXISTS:
        return True
      elif self.operator == FilterOperator.EXISTS:
        return False
      else:
        field_value = ""
    else:
      field_value = str(field_value)

    # Handle case sensitivity (use pre-computed compare_value)
    if not self.case_sensitive:
      field_value = field_value.lower()

    # Apply operator (using pre-computed self._compare_value)
    if self.operator == FilterOperator.EQUALS:
      return field_value == self._compare_value

    elif self.operator == FilterOperator.NOT_EQUALS:
      return field_value != self._compare_value

    elif self.operator == FilterOperator.CONTAINS:
      return self._compare_value in field_value

    elif self.operator == FilterOperator.NOT_CONTAINS:
      return self._compare_value not in field_value

    elif self.operator == FilterOperator.STARTS_WITH:
      return field_value.startswith(self._compare_value)

    elif self.operator == FilterOperator.ENDS_WITH:
      return field_value.endswith(self._compare_value)

    elif self.operator == FilterOperator.REGEX:
      # Use pre-compiled and validated regex pattern
      return bool(self._compiled_regex.search(field_value))

    elif self.operator == FilterOperator.IN:
      # Value should be a list
      values = [v.strip() for v in self.value.split(",")] if isinstance(self.value, str) else self.value

      if not self.case_sensitive:
        values = [str(v).lower() for v in values]

      return field_value in values

    elif self.operator == FilterOperator.NOT_IN:
      # Value should be a list
      values = [v.strip() for v in self.value.split(",")] if isinstance(self.value, str) else self.value

      if not self.case_sensitive:
        values = [str(v).lower() for v in values]

      return field_value not in values

    elif self.operator == FilterOperator.EXISTS:
      return self.get_field_value(model_data) is not None

    elif self.operator == FilterOperator.NOT_EXISTS:
      return self.get_field_value(model_data) is None

    else:
      raise ValueError(f"Unsupported string operator: {self.operator}")


# fin
