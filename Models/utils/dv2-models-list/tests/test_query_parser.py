"""
Tests for query_parser module.
"""

import pytest

from query_parser import (
  normalize_operator,
  parse_filter_expression,
  parse_value_list,
  validate_field_path,
)


class TestParseFilterExpression:
  """Tests for parse_filter_expression function."""

  def test_standard_format(self) -> None:
    """Test standard field:operator:value format."""
    field, op, value = parse_filter_expression("parent:equals:OpenAI")
    assert field == "parent"
    assert op == "equals"
    assert value == "OpenAI"

  def test_whitespace_trimmed(self) -> None:
    """Test that whitespace is trimmed."""
    field, op, value = parse_filter_expression("  parent  :  equals  :  OpenAI  ")
    assert field == "parent"
    assert op == "equals"
    assert value == "OpenAI"

  def test_value_with_colons(self) -> None:
    """Test value containing colons (e.g., URL)."""
    field, op, value = parse_filter_expression("url:contains:https://example.com")
    assert field == "url"
    assert op == "contains"
    assert value == "https://example.com"

  def test_equals_shorthand(self) -> None:
    """Test field=value shorthand format."""
    field, op, value = parse_filter_expression("parent=OpenAI")
    assert field == "parent"
    assert op == "equals"
    assert value == "OpenAI"

  def test_equals_shorthand_with_spaces(self) -> None:
    """Test equals shorthand with whitespace."""
    field, op, value = parse_filter_expression("  parent = OpenAI  ")
    assert field == "parent"
    assert op == "equals"
    assert value == "OpenAI"

  def test_nested_field(self) -> None:
    """Test nested field path."""
    field, op, value = parse_filter_expression("token_costs.input:>=:0")
    assert field == "token_costs.input"
    assert op == ">="
    assert value == "0"

  def test_operator_normalized(self) -> None:
    """Test that operators are normalized."""
    field, op, value = parse_filter_expression("model:~:gpt")
    assert op == "contains"

  def test_empty_field_raises_error(self) -> None:
    """Test that empty field raises ValueError."""
    with pytest.raises(ValueError, match="Empty field name"):
      parse_filter_expression(":equals:value")

  def test_invalid_format_raises_error(self) -> None:
    """Test that invalid format raises ValueError."""
    with pytest.raises(ValueError, match="Invalid filter expression"):
      parse_filter_expression("invalid_expression")

  def test_invalid_field_path_raises_error(self) -> None:
    """Test that invalid field path raises ValueError."""
    with pytest.raises(ValueError, match="Invalid field path"):
      parse_filter_expression("123invalid:equals:value")

  def test_invalid_field_in_shorthand_raises_error(self) -> None:
    """Test that invalid field in shorthand raises ValueError."""
    with pytest.raises(ValueError, match="Invalid field path"):
      parse_filter_expression("123invalid=value")

  def test_regex_value(self) -> None:
    """Test regex pattern as value."""
    field, op, value = parse_filter_expression("model:regex:gpt-\\d+")
    assert field == "model"
    assert op == "regex"
    assert value == "gpt-\\d+"


class TestNormalizeOperator:
  """Tests for normalize_operator function."""

  def test_equals_aliases(self) -> None:
    """Test equals operator aliases."""
    assert normalize_operator("=") == "equals"
    assert normalize_operator("eq") == "equals"
    assert normalize_operator("EQ") == "equals"

  def test_not_equals_aliases(self) -> None:
    """Test not_equals operator aliases."""
    assert normalize_operator("ne") == "not_equals"
    assert normalize_operator("<>") == "not_equals"

  def test_contains_aliases(self) -> None:
    """Test contains operator aliases."""
    assert normalize_operator("~") == "contains"
    assert normalize_operator("like") == "contains"
    assert normalize_operator("*") == "contains"

  def test_not_contains_aliases(self) -> None:
    """Test not_contains operator aliases."""
    assert normalize_operator("!~") == "not_contains"
    assert normalize_operator("not_like") == "not_contains"

  def test_starts_with_aliases(self) -> None:
    """Test starts_with operator aliases."""
    assert normalize_operator("^") == "starts_with"
    assert normalize_operator("startswith") == "starts_with"

  def test_ends_with_aliases(self) -> None:
    """Test ends_with operator aliases."""
    assert normalize_operator("$") == "ends_with"
    assert normalize_operator("endswith") == "ends_with"

  def test_regex_aliases(self) -> None:
    """Test regex operator aliases."""
    assert normalize_operator("re") == "regex"
    assert normalize_operator("regexp") == "regex"
    assert normalize_operator("match") == "regex"

  def test_comparison_aliases(self) -> None:
    """Test comparison operator aliases."""
    assert normalize_operator("lt") == "<"
    assert normalize_operator("le") == "<="
    assert normalize_operator("gt") == ">"
    assert normalize_operator("ge") == ">="

  def test_between_aliases(self) -> None:
    """Test between operator aliases."""
    assert normalize_operator("range") == "between"
    assert normalize_operator("btw") == "between"

  def test_preserves_symbolic_operators(self) -> None:
    """Test that symbolic operators are preserved."""
    assert normalize_operator("==") == "=="
    assert normalize_operator("!=") == "!="
    assert normalize_operator("<") == "<"
    assert normalize_operator("<=") == "<="
    assert normalize_operator(">") == ">"
    assert normalize_operator(">=") == ">="

  def test_unknown_operator_preserved(self) -> None:
    """Test that unknown operators are preserved lowercase."""
    assert normalize_operator("custom_op") == "custom_op"
    assert normalize_operator("CUSTOM_OP") == "custom_op"

  def test_case_insensitive(self) -> None:
    """Test that normalization is case-insensitive."""
    assert normalize_operator("LIKE") == "contains"
    assert normalize_operator("Contains") == "contains"
    assert normalize_operator("REGEX") == "regex"


class TestParseValueList:
  """Tests for parse_value_list function."""

  def test_single_value(self) -> None:
    """Test single value (no comma)."""
    result = parse_value_list("OpenAI")
    assert result == ["OpenAI"]

  def test_multiple_values(self) -> None:
    """Test comma-separated values."""
    result = parse_value_list("OpenAI,Anthropic,Google")
    assert result == ["OpenAI", "Anthropic", "Google"]

  def test_values_with_whitespace(self) -> None:
    """Test values with whitespace around them."""
    result = parse_value_list("  OpenAI  ,  Anthropic  ,  Google  ")
    assert result == ["OpenAI", "Anthropic", "Google"]

  def test_empty_string(self) -> None:
    """Test empty string."""
    result = parse_value_list("")
    assert result == [""]

  def test_trailing_comma(self) -> None:
    """Test trailing comma creates empty value."""
    result = parse_value_list("OpenAI,")
    assert result == ["OpenAI", ""]


class TestValidateFieldPath:
  """Tests for validate_field_path function."""

  def test_simple_field(self) -> None:
    """Test simple field name."""
    assert validate_field_path("model") is True
    assert validate_field_path("parent") is True
    assert validate_field_path("context_window") is True

  def test_field_with_underscore(self) -> None:
    """Test field name with underscore."""
    assert validate_field_path("model_category") is True
    assert validate_field_path("max_output_tokens") is True

  def test_field_with_numbers(self) -> None:
    """Test field name with numbers."""
    assert validate_field_path("field1") is True
    assert validate_field_path("field_2") is True

  def test_nested_field(self) -> None:
    """Test nested field path."""
    assert validate_field_path("token_costs.input") is True
    assert validate_field_path("nested.deeply.field") is True

  def test_starts_with_underscore(self) -> None:
    """Test field starting with underscore."""
    assert validate_field_path("_private") is True
    assert validate_field_path("_nested.field") is True

  def test_invalid_starts_with_number(self) -> None:
    """Test that field starting with number is invalid."""
    assert validate_field_path("123field") is False
    assert validate_field_path("1model") is False

  def test_invalid_nested_starts_with_number(self) -> None:
    """Test that nested part starting with number is invalid."""
    assert validate_field_path("field.123nested") is False

  def test_invalid_special_characters(self) -> None:
    """Test that special characters are invalid."""
    assert validate_field_path("field-name") is False
    assert validate_field_path("field@name") is False
    assert validate_field_path("field$name") is False

  def test_invalid_empty_string(self) -> None:
    """Test that empty string is invalid."""
    assert validate_field_path("") is False

  def test_invalid_just_dot(self) -> None:
    """Test that just a dot is invalid."""
    assert validate_field_path(".") is False

  def test_invalid_leading_dot(self) -> None:
    """Test that leading dot is invalid."""
    assert validate_field_path(".field") is False

  def test_invalid_trailing_dot(self) -> None:
    """Test that trailing dot is invalid."""
    assert validate_field_path("field.") is False

  def test_invalid_consecutive_dots(self) -> None:
    """Test that consecutive dots are invalid."""
    assert validate_field_path("field..nested") is False


# fin
