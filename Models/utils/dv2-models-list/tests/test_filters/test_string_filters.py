"""
Tests for StringFilter and regex validation.
"""

import pytest

from filters.base import FilterOperator
from filters.string_filters import (
  MAX_REGEX_LENGTH,
  RegexValidationError,
  StringFilter,
  validate_regex_pattern,
)


class TestRegexValidation:
  """Tests for regex pattern validation."""

  def test_valid_simple_pattern(self) -> None:
    """Test that simple patterns pass validation."""
    validate_regex_pattern(r"gpt-4")
    validate_regex_pattern(r"claude.*sonnet")
    validate_regex_pattern(r"^openai$")

  def test_pattern_too_long(self) -> None:
    """Test that overly long patterns are rejected."""
    long_pattern = "a" * (MAX_REGEX_LENGTH + 1)
    with pytest.raises(RegexValidationError, match="too long"):
      validate_regex_pattern(long_pattern)

  def test_pattern_at_max_length(self) -> None:
    """Test that patterns at max length are accepted."""
    pattern = "a" * MAX_REGEX_LENGTH
    validate_regex_pattern(pattern)  # Should not raise

  def test_nested_quantifier_rejected(self) -> None:
    """Test that nested quantifiers (ReDoS risk) are rejected."""
    with pytest.raises(RegexValidationError, match="dangerous"):
      validate_regex_pattern(r"(a+)+")

    with pytest.raises(RegexValidationError, match="dangerous"):
      validate_regex_pattern(r"([a-z]+)*")

  def test_alternation_quantifier_rejected(self) -> None:
    """Test that alternation with quantifier is rejected."""
    with pytest.raises(RegexValidationError, match="dangerous"):
      validate_regex_pattern(r"(a|b)+")

  def test_invalid_regex_syntax(self) -> None:
    """Test that invalid regex syntax is rejected."""
    with pytest.raises(RegexValidationError, match="Invalid regex"):
      validate_regex_pattern(r"[unclosed")

    with pytest.raises(RegexValidationError, match="Invalid regex"):
      validate_regex_pattern(r"(unclosed")


class TestStringFilterEquals:
  """Tests for equals/not_equals operators."""

  def test_equals_match(self, sample_model_data: dict) -> None:
    """Test exact string match."""
    filter_obj = StringFilter("parent", FilterOperator.EQUALS, "OpenAI")
    assert filter_obj.matches(sample_model_data) is True

  def test_equals_no_match(self, sample_model_data: dict) -> None:
    """Test equals with non-matching value."""
    filter_obj = StringFilter("parent", FilterOperator.EQUALS, "Anthropic")
    assert filter_obj.matches(sample_model_data) is False

  def test_equals_case_insensitive(self, sample_model_data: dict) -> None:
    """Test case-insensitive equals (default)."""
    filter_obj = StringFilter("parent", FilterOperator.EQUALS, "openai")
    assert filter_obj.matches(sample_model_data) is True

  def test_equals_case_sensitive(self, sample_model_data: dict) -> None:
    """Test case-sensitive equals."""
    filter_obj = StringFilter("parent", FilterOperator.EQUALS, "openai", case_sensitive=True)
    assert filter_obj.matches(sample_model_data) is False

    filter_obj = StringFilter("parent", FilterOperator.EQUALS, "OpenAI", case_sensitive=True)
    assert filter_obj.matches(sample_model_data) is True

  def test_not_equals_match(self, sample_model_data: dict) -> None:
    """Test not_equals with different value."""
    filter_obj = StringFilter("parent", FilterOperator.NOT_EQUALS, "Anthropic")
    assert filter_obj.matches(sample_model_data) is True

  def test_not_equals_no_match(self, sample_model_data: dict) -> None:
    """Test not_equals with same value."""
    filter_obj = StringFilter("parent", FilterOperator.NOT_EQUALS, "OpenAI")
    assert filter_obj.matches(sample_model_data) is False


class TestStringFilterContains:
  """Tests for contains/not_contains operators."""

  def test_contains_match(self, sample_model_data: dict) -> None:
    """Test substring match."""
    filter_obj = StringFilter("model", FilterOperator.CONTAINS, "gpt")
    assert filter_obj.matches(sample_model_data) is True

  def test_contains_no_match(self, sample_model_data: dict) -> None:
    """Test no substring match."""
    filter_obj = StringFilter("model", FilterOperator.CONTAINS, "claude")
    assert filter_obj.matches(sample_model_data) is False

  def test_contains_case_insensitive(self, sample_model_data: dict) -> None:
    """Test case-insensitive contains."""
    filter_obj = StringFilter("model", FilterOperator.CONTAINS, "GPT")
    assert filter_obj.matches(sample_model_data) is True

  def test_not_contains_match(self, sample_model_data: dict) -> None:
    """Test not_contains with missing substring."""
    filter_obj = StringFilter("model", FilterOperator.NOT_CONTAINS, "claude")
    assert filter_obj.matches(sample_model_data) is True

  def test_not_contains_no_match(self, sample_model_data: dict) -> None:
    """Test not_contains with present substring."""
    filter_obj = StringFilter("model", FilterOperator.NOT_CONTAINS, "gpt")
    assert filter_obj.matches(sample_model_data) is False


class TestStringFilterStartsEndsWith:
  """Tests for starts_with/ends_with operators."""

  def test_starts_with_match(self, sample_model_data: dict) -> None:
    """Test starts_with match."""
    filter_obj = StringFilter("model", FilterOperator.STARTS_WITH, "gpt")
    assert filter_obj.matches(sample_model_data) is True

  def test_starts_with_no_match(self, sample_model_data: dict) -> None:
    """Test starts_with no match."""
    filter_obj = StringFilter("model", FilterOperator.STARTS_WITH, "claude")
    assert filter_obj.matches(sample_model_data) is False

  def test_ends_with_match(self, sample_model_data: dict) -> None:
    """Test ends_with match."""
    filter_obj = StringFilter("model", FilterOperator.ENDS_WITH, "4o")
    assert filter_obj.matches(sample_model_data) is True

  def test_ends_with_no_match(self, sample_model_data: dict) -> None:
    """Test ends_with no match."""
    filter_obj = StringFilter("model", FilterOperator.ENDS_WITH, "sonnet")
    assert filter_obj.matches(sample_model_data) is False


class TestStringFilterRegex:
  """Tests for regex operator."""

  def test_regex_match(self, sample_model_data: dict) -> None:
    """Test regex match."""
    filter_obj = StringFilter("model", FilterOperator.REGEX, r"gpt-\d+o")
    assert filter_obj.matches(sample_model_data) is True

  def test_regex_no_match(self, sample_model_data: dict) -> None:
    """Test regex no match."""
    filter_obj = StringFilter("model", FilterOperator.REGEX, r"claude-\d+")
    assert filter_obj.matches(sample_model_data) is False

  def test_regex_case_insensitive(self, sample_model_data: dict) -> None:
    """Test case-insensitive regex."""
    filter_obj = StringFilter("model", FilterOperator.REGEX, r"GPT-\d+O")
    assert filter_obj.matches(sample_model_data) is True

  def test_regex_case_sensitive(self, sample_model_data: dict) -> None:
    """Test case-sensitive regex."""
    filter_obj = StringFilter("model", FilterOperator.REGEX, r"GPT-\d+O", case_sensitive=True)
    assert filter_obj.matches(sample_model_data) is False

  def test_regex_validation_error(self) -> None:
    """Test that invalid regex raises error on construction."""
    with pytest.raises(RegexValidationError):
      StringFilter("model", FilterOperator.REGEX, r"(a+)+")


class TestStringFilterInNotIn:
  """Tests for in/not_in operators."""

  def test_in_match(self, sample_model_data: dict) -> None:
    """Test in operator with matching value."""
    filter_obj = StringFilter("parent", FilterOperator.IN, "OpenAI,Anthropic,Google")
    assert filter_obj.matches(sample_model_data) is True

  def test_in_no_match(self, sample_model_data: dict) -> None:
    """Test in operator with non-matching value."""
    filter_obj = StringFilter("parent", FilterOperator.IN, "Anthropic,Google")
    assert filter_obj.matches(sample_model_data) is False

  def test_not_in_match(self, sample_model_data: dict) -> None:
    """Test not_in with non-matching values."""
    filter_obj = StringFilter("parent", FilterOperator.NOT_IN, "Anthropic,Google")
    assert filter_obj.matches(sample_model_data) is True

  def test_not_in_no_match(self, sample_model_data: dict) -> None:
    """Test not_in with matching value."""
    filter_obj = StringFilter("parent", FilterOperator.NOT_IN, "OpenAI,Anthropic")
    assert filter_obj.matches(sample_model_data) is False


class TestStringFilterExists:
  """Tests for exists/not_exists operators."""

  def test_exists_true(self, sample_model_data: dict) -> None:
    """Test exists on existing field."""
    filter_obj = StringFilter("parent", FilterOperator.EXISTS, "")
    assert filter_obj.matches(sample_model_data) is True

  def test_exists_false(self, sample_model_data: dict) -> None:
    """Test exists on missing field."""
    filter_obj = StringFilter("nonexistent", FilterOperator.EXISTS, "")
    assert filter_obj.matches(sample_model_data) is False

  def test_not_exists_true(self, sample_model_data: dict) -> None:
    """Test not_exists on missing field."""
    filter_obj = StringFilter("nonexistent", FilterOperator.NOT_EXISTS, "")
    assert filter_obj.matches(sample_model_data) is True

  def test_not_exists_false(self, sample_model_data: dict) -> None:
    """Test not_exists on existing field."""
    filter_obj = StringFilter("parent", FilterOperator.NOT_EXISTS, "")
    assert filter_obj.matches(sample_model_data) is False


class TestStringFilterNestedFields:
  """Tests for nested field access."""

  def test_nested_field_access(self, sample_model_data: dict) -> None:
    """Test accessing nested fields with dot notation."""
    filter_obj = StringFilter("nested.field", FilterOperator.EQUALS, "value")
    assert filter_obj.matches(sample_model_data) is True

  def test_nested_field_not_found(self, sample_model_data: dict) -> None:
    """Test missing nested field."""
    filter_obj = StringFilter("nested.missing", FilterOperator.EQUALS, "value")
    assert filter_obj.matches(sample_model_data) is False


class TestStringFilterRepr:
  """Tests for filter string representation."""

  def test_repr(self) -> None:
    """Test __repr__ output."""
    filter_obj = StringFilter("parent", FilterOperator.EQUALS, "OpenAI")
    repr_str = repr(filter_obj)
    assert "StringFilter" in repr_str
    assert "parent" in repr_str
    assert "equals" in repr_str
    assert "OpenAI" in repr_str


# fin
