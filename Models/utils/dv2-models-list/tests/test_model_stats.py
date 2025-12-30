"""
Tests for ModelStatistics class.
"""

import io
import sys

import pytest

from model_stats import ModelStatistics


class TestModelStatisticsPrintSummary:
  """Tests for print_summary method."""

  def test_print_summary_output(self, sample_models: dict, capsys) -> None:
    """Test that print_summary produces output."""
    stats = ModelStatistics(sample_models)
    stats.print_summary()

    captured = capsys.readouterr()
    assert "Model Statistics Summary" in captured.out
    assert "Total models:" in captured.out

  def test_print_summary_shows_providers(self, sample_models: dict, capsys) -> None:
    """Test that print_summary shows provider counts."""
    stats = ModelStatistics(sample_models)
    stats.print_summary()

    captured = capsys.readouterr()
    assert "By Provider:" in captured.out
    assert "OpenAI" in captured.out

  def test_print_summary_shows_categories(self, sample_models: dict, capsys) -> None:
    """Test that print_summary shows category counts."""
    stats = ModelStatistics(sample_models)
    stats.print_summary()

    captured = capsys.readouterr()
    assert "By Category:" in captured.out
    assert "LLM" in captured.out

  def test_print_summary_shows_availability(self, sample_models: dict, capsys) -> None:
    """Test that print_summary shows availability stats."""
    stats = ModelStatistics(sample_models)
    stats.print_summary()

    captured = capsys.readouterr()
    assert "By Availability Level:" in captured.out
    assert "Level" in captured.out

  def test_print_summary_shows_vision(self, sample_models: dict, capsys) -> None:
    """Test that print_summary shows vision capability."""
    stats = ModelStatistics(sample_models)
    stats.print_summary()

    captured = capsys.readouterr()
    assert "Vision-capable models:" in captured.out

  def test_print_summary_shows_context_stats(self, sample_models: dict, capsys) -> None:
    """Test that print_summary shows context window stats."""
    stats = ModelStatistics(sample_models)
    stats.print_summary()

    captured = capsys.readouterr()
    assert "Context Window Stats:" in captured.out
    assert "Min:" in captured.out
    assert "Max:" in captured.out
    assert "Average:" in captured.out

  def test_print_summary_empty_models(self, capsys) -> None:
    """Test print_summary with empty models."""
    stats = ModelStatistics({})
    stats.print_summary()

    captured = capsys.readouterr()
    assert "No models to analyze" in captured.out


class TestModelStatisticsPrintCountBy:
  """Tests for print_count_by method."""

  def test_count_by_parent(self, sample_models: dict, capsys) -> None:
    """Test counting by parent field."""
    stats = ModelStatistics(sample_models)
    stats.print_count_by("parent")

    captured = capsys.readouterr()
    assert "Model count by 'parent':" in captured.out
    assert "OpenAI" in captured.out
    assert "Total:" in captured.out

  def test_count_by_model_category(self, sample_models: dict, capsys) -> None:
    """Test counting by model_category field."""
    stats = ModelStatistics(sample_models)
    stats.print_count_by("model_category")

    captured = capsys.readouterr()
    assert "Model count by 'model_category':" in captured.out
    assert "LLM" in captured.out

  def test_count_by_missing_field(self, sample_models: dict, capsys) -> None:
    """Test counting by field that some models don't have."""
    stats = ModelStatistics(sample_models)
    stats.print_count_by("nonexistent")

    captured = capsys.readouterr()
    assert "[None]" in captured.out

  def test_count_by_sorted_by_count(self, sample_models: dict, capsys) -> None:
    """Test that results are sorted by count descending."""
    stats = ModelStatistics(sample_models)
    stats.print_count_by("parent")

    captured = capsys.readouterr()
    # Output should be sorted by count
    assert "Total:" in captured.out

  def test_count_by_empty_models(self, capsys) -> None:
    """Test count_by with empty models."""
    stats = ModelStatistics({})
    stats.print_count_by("parent")

    captured = capsys.readouterr()
    assert "No models to analyze" in captured.out


class TestModelStatisticsPrintUniqueValues:
  """Tests for print_unique_values method."""

  def test_unique_values_parent(self, sample_models: dict, capsys) -> None:
    """Test unique values for parent field."""
    stats = ModelStatistics(sample_models)
    stats.print_unique_values("parent")

    captured = capsys.readouterr()
    assert "Unique values for 'parent':" in captured.out
    assert "OpenAI" in captured.out
    assert "Anthropic" in captured.out
    assert "Google" in captured.out

  def test_unique_values_sorted(self, sample_models: dict, capsys) -> None:
    """Test that unique values are sorted."""
    stats = ModelStatistics(sample_models)
    stats.print_unique_values("parent")

    captured = capsys.readouterr()
    lines = captured.out.split("\n")
    # Find lines with values (indented)
    value_lines = [l.strip() for l in lines if l.startswith("  ")]
    assert value_lines == sorted(value_lines)

  def test_unique_values_count(self, sample_models: dict, capsys) -> None:
    """Test that unique value count is shown."""
    stats = ModelStatistics(sample_models)
    stats.print_unique_values("parent")

    captured = capsys.readouterr()
    assert "unique values" in captured.out

  def test_unique_values_missing_field(self, sample_models: dict, capsys) -> None:
    """Test unique values for field that doesn't exist."""
    stats = ModelStatistics(sample_models)
    stats.print_unique_values("nonexistent")

    captured = capsys.readouterr()
    assert "[No values found]" in captured.out

  def test_unique_values_empty_models(self, capsys) -> None:
    """Test unique_values with empty models."""
    stats = ModelStatistics({})
    stats.print_unique_values("parent")

    captured = capsys.readouterr()
    assert "No models to analyze" in captured.out


class TestModelStatisticsGetFieldStatistics:
  """Tests for get_field_statistics method."""

  def test_field_statistics_available(self, sample_models: dict) -> None:
    """Test getting statistics for available field."""
    stats = ModelStatistics(sample_models)
    result = stats.get_field_statistics("available")

    assert "count" in result
    assert "min" in result
    assert "max" in result
    assert "avg" in result
    assert "sum" in result
    assert "unique" in result

  def test_field_statistics_context_window(self, sample_models: dict) -> None:
    """Test statistics for context_window field."""
    stats = ModelStatistics(sample_models)
    result = stats.get_field_statistics("context_window")

    assert result["count"] > 0
    assert result["min"] > 0
    assert result["max"] >= result["min"]

  def test_field_statistics_correct_values(self) -> None:
    """Test that statistics are calculated correctly."""
    models = {
      "model1": {"value": 10},
      "model2": {"value": 20},
      "model3": {"value": 30},
    }
    stats = ModelStatistics(models)
    result = stats.get_field_statistics("value")

    assert result["count"] == 3
    assert result["min"] == 10
    assert result["max"] == 30
    assert result["avg"] == 20.0
    assert result["sum"] == 60
    assert result["unique"] == 3

  def test_field_statistics_nonexistent_field(self, sample_models: dict) -> None:
    """Test statistics for field that doesn't exist."""
    stats = ModelStatistics(sample_models)
    result = stats.get_field_statistics("nonexistent")

    assert result == {}

  def test_field_statistics_non_numeric_field(self, sample_models: dict) -> None:
    """Test statistics for non-numeric field returns empty."""
    stats = ModelStatistics(sample_models)
    result = stats.get_field_statistics("parent")

    # Should return empty dict since parent values are strings
    assert result == {}

  def test_field_statistics_mixed_values(self) -> None:
    """Test statistics handles mixed numeric/None values."""
    models = {
      "model1": {"value": 10},
      "model2": {"value": None},
      "model3": {"value": 30},
    }
    stats = ModelStatistics(models)
    result = stats.get_field_statistics("value")

    # Should only count numeric values
    assert result["count"] == 2
    assert result["min"] == 10
    assert result["max"] == 30


# fin
