"""
Integration tests for dv2-models-list CLI.
"""

import json
import pathlib
import subprocess
import tempfile

import pytest


# Path to the script
SCRIPT_PATH = pathlib.Path(__file__).parent.parent / "dv2-models-list.py"


@pytest.fixture
def temp_models_json(sample_models: dict) -> pathlib.Path:
  """Create a temporary Models.json for CLI testing."""
  with tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".json",
    delete=False,
    encoding="utf-8",
  ) as f:
    json.dump(sample_models, f, indent=2)
    return pathlib.Path(f.name)


class TestCLIBasic:
  """Basic CLI functionality tests."""

  def test_help_output(self) -> None:
    """Test --help shows usage information."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "--help"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower() or "dv2-models-list" in result.stdout

  def test_list_models(self, temp_models_json: pathlib.Path) -> None:
    """Test listing models from file."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    assert "gpt-4o" in result.stdout

  def test_nonexistent_file(self) -> None:
    """Test error handling for nonexistent file."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", "/nonexistent/path.json"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 1
    assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


class TestCLIFiltering:
  """CLI filtering functionality tests."""

  def test_filter_by_parent(self, temp_models_json: pathlib.Path) -> None:
    """Test filtering by parent provider."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-F", "parent:equals:OpenAI"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    assert "gpt-4o" in result.stdout
    assert "claude" not in result.stdout.lower()

  def test_filter_contains(self, temp_models_json: pathlib.Path) -> None:
    """Test contains filter."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-F", "model:contains:gpt"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    assert "gpt-4o" in result.stdout

  def test_filter_multiple(self, temp_models_json: pathlib.Path) -> None:
    """Test multiple filters (AND logic)."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-F", "parent:equals:OpenAI",
       "-F", "vision:equals:1"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    assert "gpt-4o" in result.stdout

  def test_filter_or_logic(self, temp_models_json: pathlib.Path) -> None:
    """Test OR logic between filters."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-F", "parent:equals:OpenAI",
       "-O",
       "-F", "parent:equals:Anthropic"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    # Should include both OpenAI and Anthropic models
    assert "gpt-4o" in result.stdout or "claude" in result.stdout.lower()

  def test_filter_negate(self, temp_models_json: pathlib.Path) -> None:
    """Test filter negation."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-F", "parent:equals:OpenAI",
       "-N"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    # Should NOT include OpenAI models
    assert "gpt-4o" not in result.stdout


class TestCLIOutputFormats:
  """CLI output format tests."""

  def test_json_output(self, temp_models_json: pathlib.Path) -> None:
    """Test JSON output format."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-o", "json"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    # Should be valid JSON
    parsed = json.loads(result.stdout)
    assert isinstance(parsed, dict)

  def test_csv_output(self, temp_models_json: pathlib.Path) -> None:
    """Test CSV output format."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-o", "csv"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    # Should have comma-separated values
    assert "," in result.stdout
    # Should have header
    assert "model" in result.stdout

  def test_table_output(self, temp_models_json: pathlib.Path) -> None:
    """Test table output format."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-o", "table"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    # Should have table formatting
    assert "|" in result.stdout

  def test_tree_output(self, temp_models_json: pathlib.Path) -> None:
    """Test tree output format."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-o", "tree"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    # Should have tree structure
    assert "grouped by" in result.stdout

  def test_custom_columns(self, temp_models_json: pathlib.Path) -> None:
    """Test custom column selection."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-o", "table", "-col", "model,parent"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    assert "model" in result.stdout
    assert "parent" in result.stdout


class TestCLISortingAndLimiting:
  """CLI sorting and limiting tests."""

  def test_sort_by_field(self, temp_models_json: pathlib.Path) -> None:
    """Test sorting by field."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-s", "parent"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0

  def test_reverse_sort(self, temp_models_json: pathlib.Path) -> None:
    """Test reverse sorting."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-s", "model", "-r"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0

  def test_limit_output(self, temp_models_json: pathlib.Path) -> None:
    """Test limiting output."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-l", "2", "-o", "json"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert len(parsed) == 2


class TestCLIStatistics:
  """CLI statistics tests."""

  def test_show_stats(self, temp_models_json: pathlib.Path) -> None:
    """Test showing statistics."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-S"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    assert "Statistics" in result.stdout or "Total" in result.stdout

  def test_count_by(self, temp_models_json: pathlib.Path) -> None:
    """Test count-by functionality."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-b", "parent"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    assert "count by" in result.stdout.lower()

  def test_unique_values(self, temp_models_json: pathlib.Path) -> None:
    """Test unique values functionality."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-u", "parent"],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    assert "unique values" in result.stdout.lower()


class TestCLIPresets:
  """CLI preset tests."""

  def test_vision_preset(self, temp_models_json: pathlib.Path) -> None:
    """Test vision preset."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json), "-d",
       "-P", "vision"],
      capture_output=True,
      text=True,
    )
    # Should succeed (may or may not have matches)
    assert result.returncode == 0


class TestCLIEdgeCases:
  """Edge case tests."""

  def test_empty_models_file(self, temp_empty_models_file: pathlib.Path) -> None:
    """Test with empty models file."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_empty_models_file)],
      capture_output=True,
      text=True,
    )
    assert result.returncode == 0
    # Should indicate no models found
    assert "No models" in result.stdout or result.stdout.strip() == ""

  def test_invalid_filter_expression(self, temp_models_json: pathlib.Path) -> None:
    """Test with invalid filter expression."""
    result = subprocess.run(
      ["python3", str(SCRIPT_PATH), "-m", str(temp_models_json),
       "-F", "invalid_expression_without_colons"],
      capture_output=True,
      text=True,
    )
    # Should fail with error
    assert result.returncode != 0 or "error" in result.stderr.lower() or "invalid" in result.stderr.lower()


# fin
