"""
Tests for CSVFormatter.
"""

import csv
import io

import pytest

from formatters import CSVFormatter


class TestCSVFormatter:
  """Tests for CSVFormatter."""

  def test_format_with_header(self, sample_models: dict) -> None:
    """Test CSV format includes header."""
    formatter = CSVFormatter()
    output = formatter.format(sample_models, show_header=True)

    # Parse as CSV
    reader = csv.reader(io.StringIO(output))
    rows = list(reader)

    # First row should be header
    header = rows[0]
    assert "model" in header
    assert "alias" in header

  def test_format_without_header(self, sample_models: dict) -> None:
    """Test CSV format without header."""
    formatter = CSVFormatter()
    output = formatter.format(sample_models, show_header=False)

    # Parse as CSV
    reader = csv.reader(io.StringIO(output))
    rows = list(reader)

    # First row should be data, not header
    first_row = rows[0]
    # Should be a model name, not column name
    assert first_row[0] in sample_models

  def test_format_custom_columns(self, sample_models: dict) -> None:
    """Test CSV with custom columns."""
    formatter = CSVFormatter()
    output = formatter.format(sample_models, columns=["model", "parent"], show_header=True)

    reader = csv.reader(io.StringIO(output))
    rows = list(reader)

    header = rows[0]
    assert header == ["model", "parent"]

    # Data rows should have 2 columns
    for row in rows[1:]:
      assert len(row) == 2

  def test_format_sorted_models(self, sample_models: dict) -> None:
    """Test that CSV output is sorted by model name."""
    formatter = CSVFormatter()
    output = formatter.format(sample_models, show_header=False)

    reader = csv.reader(io.StringIO(output))
    rows = list(reader)

    # Get model names (first column)
    model_names = [row[0] for row in rows]
    assert model_names == sorted(model_names)

  def test_format_empty_models(self) -> None:
    """Test CSV format with empty models."""
    formatter = CSVFormatter()
    output = formatter.format({})
    assert output == ""

  def test_format_special_characters(self) -> None:
    """Test CSV properly escapes special characters."""
    models = {
      "model-with-comma": {
        "alias": "test,alias",
        "parent": "Test \"Provider\"",
        "model_category": "LLM",
        "available": 9,
        "enabled": 9,
      }
    }
    formatter = CSVFormatter()
    output = formatter.format(models, columns=["model", "alias", "parent"], show_header=False)

    # Should be parseable without errors
    reader = csv.reader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0][1] == "test,alias"
    assert rows[0][2] == 'Test "Provider"'


# fin
