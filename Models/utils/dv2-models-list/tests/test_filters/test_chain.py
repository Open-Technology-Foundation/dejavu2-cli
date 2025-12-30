"""
Tests for FilterChain.
"""

import pytest

from filters import FilterChain


class TestFilterChainBasic:
  """Tests for basic FilterChain functionality."""

  def test_empty_chain_matches_all(self, sample_model_data: dict) -> None:
    """Test that empty filter chain matches everything."""
    chain = FilterChain()
    assert chain.matches(sample_model_data) is True

  def test_single_filter_match(self, sample_model_data: dict) -> None:
    """Test chain with single matching filter."""
    chain = FilterChain()
    chain.add_filter("parent", "equals", "OpenAI")
    assert chain.matches(sample_model_data) is True

  def test_single_filter_no_match(self, sample_model_data: dict) -> None:
    """Test chain with single non-matching filter."""
    chain = FilterChain()
    chain.add_filter("parent", "equals", "Anthropic")
    assert chain.matches(sample_model_data) is False

  def test_len(self) -> None:
    """Test __len__ returns filter count."""
    chain = FilterChain()
    assert len(chain) == 0

    chain.add_filter("parent", "equals", "OpenAI")
    assert len(chain) == 1

    chain.add_filter("model", "contains", "gpt")
    assert len(chain) == 2

  def test_clear(self) -> None:
    """Test clearing all filters."""
    chain = FilterChain()
    chain.add_filter("parent", "equals", "OpenAI")
    chain.add_filter("model", "contains", "gpt")
    assert len(chain) == 2

    chain.clear()
    assert len(chain) == 0


class TestFilterChainAndLogic:
  """Tests for AND logic (default)."""

  def test_and_all_match(self, sample_model_data: dict) -> None:
    """Test AND logic when all filters match."""
    chain = FilterChain(use_or=False)
    chain.add_filter("parent", "equals", "OpenAI")
    chain.add_filter("model", "contains", "gpt")
    chain.add_filter("available", ">=", "5")
    assert chain.matches(sample_model_data) is True

  def test_and_one_fails(self, sample_model_data: dict) -> None:
    """Test AND logic when one filter fails."""
    chain = FilterChain(use_or=False)
    chain.add_filter("parent", "equals", "OpenAI")
    chain.add_filter("model", "contains", "claude")  # Should fail
    assert chain.matches(sample_model_data) is False

  def test_and_all_fail(self, sample_model_data: dict) -> None:
    """Test AND logic when all filters fail."""
    chain = FilterChain(use_or=False)
    chain.add_filter("parent", "equals", "Anthropic")
    chain.add_filter("model", "contains", "claude")
    assert chain.matches(sample_model_data) is False


class TestFilterChainOrLogic:
  """Tests for OR logic."""

  def test_or_all_match(self, sample_model_data: dict) -> None:
    """Test OR logic when all filters match."""
    chain = FilterChain(use_or=True)
    chain.add_filter("parent", "equals", "OpenAI")
    chain.add_filter("model", "contains", "gpt")
    assert chain.matches(sample_model_data) is True

  def test_or_one_matches(self, sample_model_data: dict) -> None:
    """Test OR logic when one filter matches."""
    chain = FilterChain(use_or=True)
    chain.add_filter("parent", "equals", "Anthropic")  # Fails
    chain.add_filter("model", "contains", "gpt")  # Matches
    assert chain.matches(sample_model_data) is True

  def test_or_none_match(self, sample_model_data: dict) -> None:
    """Test OR logic when no filters match."""
    chain = FilterChain(use_or=True)
    chain.add_filter("parent", "equals", "Anthropic")
    chain.add_filter("model", "contains", "claude")
    assert chain.matches(sample_model_data) is False


class TestFilterChainNegation:
  """Tests for filter chain negation."""

  def test_negate_match_becomes_no_match(self, sample_model_data: dict) -> None:
    """Test negation turns match into no match."""
    chain = FilterChain(negate=True)
    chain.add_filter("parent", "equals", "OpenAI")
    assert chain.matches(sample_model_data) is False

  def test_negate_no_match_becomes_match(self, sample_model_data: dict) -> None:
    """Test negation turns no match into match."""
    chain = FilterChain(negate=True)
    chain.add_filter("parent", "equals", "Anthropic")
    assert chain.matches(sample_model_data) is True

  def test_negate_with_or_logic(self, sample_model_data: dict) -> None:
    """Test negation with OR logic."""
    chain = FilterChain(use_or=True, negate=True)
    chain.add_filter("parent", "equals", "OpenAI")  # Matches
    chain.add_filter("model", "contains", "gpt")  # Matches
    # OR result is True, negated becomes False
    assert chain.matches(sample_model_data) is False


class TestFilterChainOperatorMapping:
  """Tests for operator string to enum mapping."""

  def test_equals_operators(self, sample_model_data: dict) -> None:
    """Test various 'equals' operator strings."""
    chain = FilterChain()
    chain.add_filter("available", "equals", "9")
    assert chain.matches(sample_model_data) is True

    chain.clear()
    chain.add_filter("available", "eq", "9")
    assert chain.matches(sample_model_data) is True

    chain.clear()
    chain.add_filter("available", "==", "9")
    assert chain.matches(sample_model_data) is True

  def test_not_equals_operators(self, sample_model_data: dict) -> None:
    """Test various 'not equals' operator strings."""
    chain = FilterChain()
    chain.add_filter("available", "not_equals", "5")
    assert chain.matches(sample_model_data) is True

    chain.clear()
    chain.add_filter("available", "ne", "5")
    assert chain.matches(sample_model_data) is True

    chain.clear()
    chain.add_filter("available", "!=", "5")
    assert chain.matches(sample_model_data) is True

  def test_comparison_operators(self, sample_model_data: dict) -> None:
    """Test comparison operator strings."""
    chain = FilterChain()
    chain.add_filter("available", "<", "10")
    assert chain.matches(sample_model_data) is True

    chain.clear()
    chain.add_filter("available", "<=", "9")
    assert chain.matches(sample_model_data) is True

    chain.clear()
    chain.add_filter("available", ">", "8")
    assert chain.matches(sample_model_data) is True

    chain.clear()
    chain.add_filter("available", ">=", "9")
    assert chain.matches(sample_model_data) is True

  def test_unknown_operator_raises_error(self) -> None:
    """Test that unknown operator raises ValueError."""
    chain = FilterChain()
    with pytest.raises(ValueError, match="Unknown operator"):
      chain.add_filter("field", "unknown_op", "value")


class TestFilterChainCaseSensitivity:
  """Tests for case sensitivity handling."""

  def test_case_insensitive_default(self, sample_model_data: dict) -> None:
    """Test case-insensitive matching by default."""
    chain = FilterChain()
    chain.add_filter("parent", "equals", "openai", case_sensitive=False)
    assert chain.matches(sample_model_data) is True

  def test_case_sensitive(self, sample_model_data: dict) -> None:
    """Test case-sensitive matching when specified."""
    chain = FilterChain()
    chain.add_filter("parent", "equals", "openai", case_sensitive=True)
    assert chain.matches(sample_model_data) is False

    chain.clear()
    chain.add_filter("parent", "equals", "OpenAI", case_sensitive=True)
    assert chain.matches(sample_model_data) is True


class TestFilterChainNumericFields:
  """Tests for automatic numeric field detection."""

  def test_numeric_field_uses_numeric_filter(self, sample_model_data: dict) -> None:
    """Test that known numeric fields use NumericFilter."""
    chain = FilterChain()
    chain.add_filter("available", ">=", "5")
    assert chain.matches(sample_model_data) is True

  def test_context_window_filter(self, sample_model_data: dict) -> None:
    """Test filtering by context_window."""
    chain = FilterChain()
    chain.add_filter("context_window", ">=", "100000")
    assert chain.matches(sample_model_data) is True


class TestFilterChainRepr:
  """Tests for filter chain string representation."""

  def test_repr_and(self) -> None:
    """Test __repr__ with AND logic."""
    chain = FilterChain(use_or=False)
    repr_str = repr(chain)
    assert "AND" in repr_str

  def test_repr_or(self) -> None:
    """Test __repr__ with OR logic."""
    chain = FilterChain(use_or=True)
    repr_str = repr(chain)
    assert "OR" in repr_str

  def test_repr_negated(self) -> None:
    """Test __repr__ with negation."""
    chain = FilterChain(negate=True)
    repr_str = repr(chain)
    assert "NOT" in repr_str


# fin
