"""
Parse filter expressions from command line arguments.
"""

import re


def parse_filter_expression(expr: str) -> tuple[str, str, str]:
  """
  Parse a filter expression in the format "field:operator:value".

  Args:
    expr: Filter expression string

  Returns:
    Tuple of (field, operator, value)

  Raises:
    ValueError: If expression format is invalid
  """
  # Handle special case where value might contain colons (e.g., in regex patterns)
  # Split only on first two colons
  parts = expr.split(":", 2)

  if len(parts) < 3:
    # Try alternative separators
    if "=" in expr:
      # Handle field=value as equals operator
      field, value = expr.split("=", 1)
      field = field.strip()
      if not validate_field_path(field):
        raise ValueError(f"Invalid field path '{field}' in expression: '{expr}'")
      return field, "equals", value.strip()
    else:
      raise ValueError(f"Invalid filter expression: '{expr}'. Expected format: 'field:operator:value' or 'field=value'")

  field, operator, value = parts

  # Clean up whitespace
  field = field.strip()
  operator = operator.strip()
  value = value.strip()

  # Validate field name
  if not field:
    raise ValueError(f"Empty field name in filter expression: '{expr}'")

  if not validate_field_path(field):
    raise ValueError(f"Invalid field path '{field}' in expression: '{expr}'")

  # Normalize operator aliases
  operator = normalize_operator(operator)

  return field, operator, value


def normalize_operator(operator: str) -> str:
  """
  Normalize operator aliases to standard names.

  Args:
    operator: Operator string (may be an alias)

  Returns:
    Normalized operator name
  """
  # Define operator aliases
  aliases = {
    "=": "equals",
    "eq": "equals",
    "==": "==",
    "!=": "!=",
    "ne": "not_equals",
    "<>": "not_equals",
    "~": "contains",
    "like": "contains",
    "*": "contains",
    "!~": "not_contains",
    "not_like": "not_contains",
    "^": "starts_with",
    "startswith": "starts_with",
    "$": "ends_with",
    "endswith": "ends_with",
    "re": "regex",
    "regexp": "regex",
    "match": "regex",
    "lt": "<",
    "le": "<=",
    "gt": ">",
    "ge": ">=",
    "range": "between",
    "btw": "between",
  }

  # Normalize to lowercase
  op_lower = operator.lower()

  # Return alias mapping or original
  return aliases.get(op_lower, op_lower)


def parse_value_list(value: str) -> list:
  """
  Parse a comma-separated value list.

  Args:
    value: Comma-separated string

  Returns:
    List of parsed values
  """
  # Handle quoted values
  if "," not in value:
    return [value.strip()]

  # Simple split for now (could be enhanced to handle quoted commas)
  return [v.strip() for v in value.split(",")]


def validate_field_path(field: str) -> bool:
  """
  Validate a field path (supports nested fields like 'token_costs.input').

  Args:
    field: Field path to validate

  Returns:
    True if valid, False otherwise
  """
  # Field should contain only alphanumeric, underscore, and dots
  pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$"
  return bool(re.match(pattern, field))


# fin
