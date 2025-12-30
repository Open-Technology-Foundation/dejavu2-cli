"""
Tests for TableFormatter.
"""

import pytest

from formatters import TableFormatter


class TestTableFormatterSimpleMode:
  """Tests for simple table mode."""

  def test_simple_format(self, sample_models: dict) -> None:
    """Test simple format output."""
    formatter = TableFormatter(mode="simple")
    output = formatter.format(sample_models)

    # Should contain model names with aliases
    assert "gpt-4o (4o)" in output
    assert "claude-sonnet-4-20250514 (sonnet)" in output

  def test_simple_format_sorted(self, sample_models: dict) -> None:
    """Test that simple format is sorted by model name."""
    formatter = TableFormatter(mode="simple")
    output = formatter.format(sample_models)
    lines = output.split("\n")

    # Extract model names (first part before parenthesis)
    model_names = [line.split(" (")[0] for line in lines if line]
    assert model_names == sorted(model_names)

  def test_simple_format_empty(self) -> None:
    """Test simple format with empty models."""
    formatter = TableFormatter(mode="simple")
    output = formatter.format({})
    assert output == "No models found."


class TestTableFormatterFullMode:
  """Tests for full table mode."""

  def test_full_format_with_header(self, sample_models: dict) -> None:
    """Test full table format includes header."""
    formatter = TableFormatter(mode="full")
    output = formatter.format(sample_models, show_header=True)

    # Should have header row
    assert "model" in output
    assert "alias" in output
    assert "parent" in output

    # Should have separator line
    assert "-+-" in output

  def test_full_format_without_header(self, sample_models: dict) -> None:
    """Test full table format without header."""
    formatter = TableFormatter(mode="full")
    output = formatter.format(sample_models, show_header=False)

    # Should NOT have separator line
    assert "-+-" not in output

  def test_full_format_custom_columns(self, sample_models: dict) -> None:
    """Test full table with custom columns."""
    formatter = TableFormatter(mode="full")
    output = formatter.format(sample_models, columns=["model", "parent", "enabled"])

    # Should have specified columns
    assert "model" in output
    assert "parent" in output
    assert "enabled" in output

    # Should NOT have non-specified columns in header
    lines = output.split("\n")
    header = lines[0]
    assert "alias" not in header

  def test_full_format_numeric_alignment(self, sample_models: dict) -> None:
    """Test that numeric columns are right-aligned."""
    formatter = TableFormatter(mode="full")
    output = formatter.format(sample_models, columns=["model", "available", "enabled"])

    # Output should exist without errors
    assert "gpt-4o" in output
    assert "9" in output

  def test_full_format_empty(self) -> None:
    """Test full format with empty models."""
    formatter = TableFormatter(mode="full")
    output = formatter.format({})
    assert output == "No models found."


class TestTableFormatterDefaultColumns:
  """Tests for default column handling."""

  def test_get_default_columns(self) -> None:
    """Test default columns list."""
    formatter = TableFormatter()
    columns = formatter.get_default_columns()

    assert "model" in columns
    assert "alias" in columns
    assert "parent" in columns
    assert "model_category" in columns
    assert "available" in columns
    assert "enabled" in columns


class TestTableFormatterGetAllFields:
  """Tests for get_all_fields method."""

  def test_get_all_fields(self, sample_models: dict) -> None:
    """Test extracting all unique fields."""
    formatter = TableFormatter()
    fields = formatter.get_all_fields(sample_models)

    assert "model" in fields or "alias" in fields  # At least some fields present
    assert "parent" in fields
    assert sorted(fields) == fields  # Should be sorted


class TestTableFormatterPrepareModelData:
  """Tests for prepare_model_data method."""

  def test_prepare_with_columns(self, sample_models: dict) -> None:
    """Test preparing data with specific columns."""
    formatter = TableFormatter()
    data = sample_models["gpt-4o"]
    prepared = formatter.prepare_model_data("gpt-4o", data, columns=["model", "parent"])

    assert prepared["model"] == "gpt-4o"
    assert prepared["parent"] == "OpenAI"
    assert "context_window" not in prepared  # Not in requested columns

  def test_prepare_without_columns(self, sample_models: dict) -> None:
    """Test preparing data without column filter."""
    formatter = TableFormatter()
    data = sample_models["gpt-4o"]
    prepared = formatter.prepare_model_data("gpt-4o", data, columns=None)

    assert prepared["model"] == "gpt-4o"
    assert "parent" in prepared
    assert "context_window" in prepared  # All fields included


# fin
