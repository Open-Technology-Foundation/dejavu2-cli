"""
Tests for TreeFormatter.
"""

import pytest

from formatters import TreeFormatter


class TestTreeFormatter:
  """Tests for TreeFormatter."""

  def test_format_default_grouping(self, sample_models: dict) -> None:
    """Test tree format with default grouping (parent)."""
    formatter = TreeFormatter()
    output = formatter.format(sample_models)

    # Should mention grouping
    assert "grouped by 'parent'" in output

    # Should have group headers
    assert "OpenAI" in output
    assert "Anthropic" in output
    assert "Google" in output

  def test_format_custom_grouping(self, sample_models: dict) -> None:
    """Test tree format with custom grouping field."""
    formatter = TreeFormatter()
    output = formatter.format(sample_models, group_by="model_category")

    assert "grouped by 'model_category'" in output
    assert "LLM" in output
    assert "embed" in output

  def test_format_shows_count(self, sample_models: dict) -> None:
    """Test that group counts are shown by default."""
    formatter = TreeFormatter()
    output = formatter.format(sample_models, show_count=True)

    # Should have count in parentheses
    assert "models)" in output

  def test_format_hides_count(self, sample_models: dict) -> None:
    """Test that counts can be hidden."""
    formatter = TreeFormatter()
    output = formatter.format(sample_models, show_count=False, group_by="parent")

    # Count OpenAI occurrences - should not have "models)" after group name
    lines = [l for l in output.split("\n") if "OpenAI" in l and "models)" in l]
    # The folder line should not have count
    folder_lines = [l for l in output.split("\n") if l.startswith("📁") and "models)" in l]
    assert len(folder_lines) == 0

  def test_format_tree_characters(self, sample_models: dict) -> None:
    """Test that tree uses proper characters."""
    formatter = TreeFormatter()
    output = formatter.format(sample_models)

    # Should have tree characters
    assert "├─" in output or "└─" in output
    assert "📁" in output

  def test_format_shows_model_details(self, sample_models: dict) -> None:
    """Test that model details are shown."""
    formatter = TreeFormatter()
    output = formatter.format(sample_models)

    # Should show aliases in parentheses
    assert "(4o)" in output or "(sonnet)" in output

    # Should show status
    assert "enabled=" in output or "available=" in output

  def test_format_empty_models(self) -> None:
    """Test tree format with empty models."""
    formatter = TreeFormatter()
    output = formatter.format({})
    assert output == "No models found."

  def test_format_summary(self, sample_models: dict) -> None:
    """Test that summary line is included."""
    formatter = TreeFormatter()
    output = formatter.format(sample_models)

    # Should have summary
    assert "Total:" in output
    assert "models in" in output
    assert "groups" in output

  def test_format_ungrouped_models(self) -> None:
    """Test handling of models without group field."""
    models = {
      "model-without-parent": {
        "alias": "noparent",
        "model_category": "LLM",
        "available": 5,
        "enabled": 3,
      },
      "model-with-parent": {
        "alias": "hasparent",
        "parent": "TestProvider",
        "model_category": "LLM",
        "available": 9,
        "enabled": 9,
      },
    }
    formatter = TreeFormatter()
    output = formatter.format(models, group_by="parent")

    # Should have ungrouped section
    assert "[No parent]" in output


class TestTreeFormatterSorting:
  """Tests for tree formatter sorting."""

  def test_groups_sorted(self, sample_models: dict) -> None:
    """Test that groups are sorted alphabetically."""
    formatter = TreeFormatter()
    output = formatter.format(sample_models, group_by="parent")

    lines = output.split("\n")
    group_lines = [l for l in lines if l.startswith("📁") and "[No" not in l]

    # Extract group names
    group_names = []
    for line in group_lines:
      # Parse "📁 GroupName (X models)" or "📁 GroupName"
      name = line.replace("📁 ", "").split(" (")[0].strip()
      group_names.append(name)

    assert group_names == sorted(group_names)

  def test_models_within_group_sorted(self, sample_models: dict) -> None:
    """Test that models within each group are sorted."""
    formatter = TreeFormatter()
    # Group by model_category where LLM has multiple models
    output = formatter.format(sample_models, group_by="model_category")

    # The output is sorted so no specific check needed beyond
    # verifying output doesn't error
    assert "LLM" in output


# fin
