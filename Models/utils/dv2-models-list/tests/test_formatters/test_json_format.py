"""
Tests for JSONFormatter.
"""

import json

import pytest

from formatters import JSONFormatter


class TestJSONFormatter:
  """Tests for JSONFormatter."""

  def test_format_all_models(self, sample_models: dict) -> None:
    """Test formatting all models as JSON."""
    formatter = JSONFormatter()
    output = formatter.format(sample_models)

    # Should be valid JSON
    parsed = json.loads(output)
    assert isinstance(parsed, dict)
    assert "gpt-4o" in parsed

  def test_format_with_custom_columns(self, sample_models: dict) -> None:
    """Test formatting with custom columns."""
    formatter = JSONFormatter()
    output = formatter.format(sample_models, columns=["model", "parent", "enabled"])

    parsed = json.loads(output)
    gpt4o = parsed["gpt-4o"]

    # Should have specified columns (except 'model' which is removed as redundant)
    assert "parent" in gpt4o
    assert "enabled" in gpt4o
    assert "context_window" not in gpt4o

  def test_format_sorted_keys(self, sample_models: dict) -> None:
    """Test that JSON output has sorted keys."""
    formatter = JSONFormatter()
    output = formatter.format(sample_models)

    # JSON should be sorted
    parsed = json.loads(output)
    model_keys = list(parsed.keys())
    assert model_keys == sorted(model_keys)

  def test_format_indented(self, sample_models: dict) -> None:
    """Test that JSON is indented."""
    formatter = JSONFormatter()
    output = formatter.format(sample_models, indent=4)

    # Should have indentation
    assert "\n    " in output or "\n  " in output

  def test_format_empty_models(self) -> None:
    """Test formatting empty models dict."""
    formatter = JSONFormatter()
    output = formatter.format({})

    parsed = json.loads(output)
    assert parsed == {}

  def test_format_preserves_data_types(self, sample_models: dict) -> None:
    """Test that data types are preserved in JSON."""
    formatter = JSONFormatter()
    output = formatter.format(sample_models)

    parsed = json.loads(output)
    gpt4o = parsed["gpt-4o"]

    # Numeric fields should remain numeric
    assert isinstance(gpt4o["available"], int)
    assert isinstance(gpt4o["enabled"], int)
    assert isinstance(gpt4o["context_window"], int)


# fin
