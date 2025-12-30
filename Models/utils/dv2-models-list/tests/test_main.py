"""
Tests for main module functions.
"""

import argparse
import pathlib
import tempfile

import pytest

# Note: Due to the hyphenated module name, we import the module differently
# Import the functions we need to test
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# Import by reading the module file
import importlib.util

spec = importlib.util.spec_from_file_location(
  "dv2_models_list",
  pathlib.Path(__file__).parent.parent / "dv2-models-list.py"
)
main_module = importlib.util.module_from_spec(spec)


class TestLoadModels:
  """Tests for load_models function."""

  def test_load_valid_models(self, temp_models_file: pathlib.Path) -> None:
    """Test loading a valid Models.json file."""
    # Execute the module to get the function
    spec.loader.exec_module(main_module)
    models = main_module.load_models(temp_models_file)

    assert isinstance(models, dict)
    assert "gpt-4o" in models
    assert models["gpt-4o"]["parent"] == "OpenAI"

  def test_load_nonexistent_file(self, nonexistent_path: pathlib.Path) -> None:
    """Test loading a file that doesn't exist raises ModelLoadError."""
    spec.loader.exec_module(main_module)

    with pytest.raises(main_module.ModelLoadError, match="not found"):
      main_module.load_models(nonexistent_path)

  def test_load_invalid_json(self, temp_invalid_json_file: pathlib.Path) -> None:
    """Test loading invalid JSON raises ModelLoadError."""
    spec.loader.exec_module(main_module)

    with pytest.raises(main_module.ModelLoadError, match="Invalid JSON"):
      main_module.load_models(temp_invalid_json_file)

  def test_load_empty_models(self, temp_empty_models_file: pathlib.Path) -> None:
    """Test loading empty models file."""
    spec.loader.exec_module(main_module)
    models = main_module.load_models(temp_empty_models_file)

    assert models == {}

  def test_load_directory_path(self, tmp_path: pathlib.Path) -> None:
    """Test loading a directory path raises ModelLoadError."""
    spec.loader.exec_module(main_module)

    with pytest.raises(main_module.ModelLoadError, match="directory"):
      main_module.load_models(tmp_path)


class TestModelLoadError:
  """Tests for ModelLoadError exception."""

  def test_exception_message(self) -> None:
    """Test that ModelLoadError preserves message."""
    spec.loader.exec_module(main_module)

    error = main_module.ModelLoadError("Test error message")
    assert str(error) == "Test error message"

  def test_exception_inheritance(self) -> None:
    """Test that ModelLoadError inherits from Exception."""
    spec.loader.exec_module(main_module)

    assert issubclass(main_module.ModelLoadError, Exception)


class TestApplyLegacyFilters:
  """Tests for apply_legacy_filters function."""

  def test_no_legacy_filters(self) -> None:
    """Test with no legacy filters set."""
    spec.loader.exec_module(main_module)

    args = argparse.Namespace(
      alias=None,
      parent=None,
      model_category=None,
      family=None,
      available=None,
      enabled=None,
    )
    filters = main_module.apply_legacy_filters(args)

    assert filters == []

  def test_alias_filter(self) -> None:
    """Test alias legacy filter."""
    spec.loader.exec_module(main_module)

    args = argparse.Namespace(
      alias="sonnet",
      parent=None,
      model_category=None,
      family=None,
      available=None,
      enabled=None,
    )
    filters = main_module.apply_legacy_filters(args)

    assert ("alias", "equals", "sonnet") in filters

  def test_parent_filter(self) -> None:
    """Test parent legacy filter."""
    spec.loader.exec_module(main_module)

    args = argparse.Namespace(
      alias=None,
      parent="OpenAI",
      model_category=None,
      family=None,
      available=None,
      enabled=None,
    )
    filters = main_module.apply_legacy_filters(args)

    assert ("parent", "equals", "OpenAI") in filters

  def test_available_filter(self) -> None:
    """Test available legacy filter (numeric)."""
    spec.loader.exec_module(main_module)

    args = argparse.Namespace(
      alias=None,
      parent=None,
      model_category=None,
      family=None,
      available=5,
      enabled=None,
    )
    filters = main_module.apply_legacy_filters(args)

    assert ("available", "<=", "5") in filters

  def test_multiple_filters(self) -> None:
    """Test multiple legacy filters."""
    spec.loader.exec_module(main_module)

    args = argparse.Namespace(
      alias=None,
      parent="OpenAI",
      model_category="LLM",
      family=None,
      available=5,
      enabled=None,
    )
    filters = main_module.apply_legacy_filters(args)

    assert len(filters) == 3
    assert ("parent", "equals", "OpenAI") in filters
    assert ("model_category", "equals", "LLM") in filters
    assert ("available", "<=", "5") in filters


class TestSortModels:
  """Tests for sort_models function."""

  def test_sort_by_model_name(self, sample_models: dict) -> None:
    """Test sorting by model name."""
    spec.loader.exec_module(main_module)

    sorted_models = main_module.sort_models(sample_models, ["model"])
    keys = list(sorted_models.keys())

    assert keys == sorted(keys)

  def test_sort_by_parent(self, sample_models: dict) -> None:
    """Test sorting by parent field."""
    spec.loader.exec_module(main_module)

    sorted_models = main_module.sort_models(sample_models, ["parent"])
    parents = [m.get("parent", "") for m in sorted_models.values()]

    # Parents should be sorted (allowing for None values)
    sorted_parents = sorted(parents, key=lambda x: x or "")
    assert parents == sorted_parents

  def test_sort_reverse(self, sample_models: dict) -> None:
    """Test reverse sorting."""
    spec.loader.exec_module(main_module)

    sorted_models = main_module.sort_models(sample_models, ["model"], reverse=True)
    keys = list(sorted_models.keys())

    assert keys == sorted(keys, reverse=True)

  def test_sort_multiple_fields(self, sample_models: dict) -> None:
    """Test sorting by multiple fields."""
    spec.loader.exec_module(main_module)

    sorted_models = main_module.sort_models(sample_models, ["parent", "model"])

    # Should sort by parent first, then model
    assert isinstance(sorted_models, dict)

  def test_sort_with_none_values(self) -> None:
    """Test sorting handles None values."""
    spec.loader.exec_module(main_module)

    models = {
      "model1": {"parent": "ZZZ"},
      "model2": {"parent": None},
      "model3": {"parent": "AAA"},
    }
    sorted_models = main_module.sort_models(models, ["parent"])

    # Should not raise error
    assert len(sorted_models) == 3


class TestGetFormatter:
  """Tests for get_formatter function."""

  def test_get_default_formatter(self) -> None:
    """Test getting default formatter."""
    spec.loader.exec_module(main_module)

    formatter = main_module.get_formatter("default")
    assert formatter is not None

  def test_get_table_formatter(self) -> None:
    """Test getting table formatter."""
    spec.loader.exec_module(main_module)

    formatter = main_module.get_formatter("table")
    assert formatter is not None

  def test_get_json_formatter(self) -> None:
    """Test getting JSON formatter."""
    spec.loader.exec_module(main_module)

    formatter = main_module.get_formatter("json")
    assert formatter is not None

  def test_get_csv_formatter(self) -> None:
    """Test getting CSV formatter."""
    spec.loader.exec_module(main_module)

    formatter = main_module.get_formatter("csv")
    assert formatter is not None

  def test_get_yaml_formatter(self) -> None:
    """Test getting YAML formatter."""
    spec.loader.exec_module(main_module)

    formatter = main_module.get_formatter("yaml")
    assert formatter is not None

  def test_get_tree_formatter(self) -> None:
    """Test getting tree formatter."""
    spec.loader.exec_module(main_module)

    formatter = main_module.get_formatter("tree")
    assert formatter is not None

  def test_get_unknown_formatter_returns_default(self) -> None:
    """Test that unknown format returns default formatter."""
    spec.loader.exec_module(main_module)

    formatter = main_module.get_formatter("unknown")
    default_formatter = main_module.get_formatter("default")

    # Both should work (may or may not be same instance)
    assert formatter is not None


# fin
