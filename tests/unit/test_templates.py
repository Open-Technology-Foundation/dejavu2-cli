"""
Unit tests for template handling in dejavu2-cli.
"""

import json
import os
import sys
from unittest.mock import MagicMock, mock_open, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from errors import ConfigurationError, TemplateError
from templates import get_template, list_template_names, list_templates, load_template_data


class TestTemplates:
  """Test template handling functionality."""

  def setup_method(self):
    """Clear module-level cache before each test."""
    import templates

    templates._templates_cache.clear()
    templates._cache_mtime.clear()

  def test_load_template_data(self):
    """Test loading template data from a mock JSON file."""
    mock_templates = {
      "Template 1": {"category": "General", "systemprompt": "You are a helpful assistant.", "model": "gpt-4o", "temperature": 0.7},
      "Template 2": {"category": "Code", "systemprompt": "You are a code assistant.", "model": "claude-3-5-sonnet", "temperature": 0.1},
    }

    mock_json = json.dumps(mock_templates)

    with patch("os.path.exists", return_value=True), patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)):
      templates = load_template_data("dummy_path.json")

      assert "Template 1" in templates
      assert "Template 2" in templates
      assert templates["Template 1"]["category"] == "General"
      assert templates["Template 2"]["model"] == "claude-3-5-sonnet"

  def test_load_template_data_file_not_found(self):
    """Test loading templates when the JSON file doesn't exist."""
    with patch("os.path.exists", return_value=False), pytest.raises(ConfigurationError, match="Template file not found"):
      load_template_data("nonexistent.json")

  def test_load_template_data_invalid_json(self):
    """Test loading templates with invalid JSON content."""
    with patch("os.path.exists", return_value=True), patch("os.path.getmtime", return_value=1234567890.0), patch(
      "builtins.open", mock_open(read_data='{"invalid": json')
    ):
      with pytest.raises(TemplateError, match="Invalid JSON"):
        load_template_data("invalid.json")

  def test_load_template_data_invalid_format(self):
    """Test loading templates with invalid format (not a dict)."""
    with patch("os.path.exists", return_value=True), patch("os.path.getmtime", return_value=1234567890.0), patch(
      "builtins.open", mock_open(read_data='["list", "not", "dict"]')
    ):
      with pytest.raises(TemplateError, match="Invalid template format"):
        load_template_data("invalid.json")

  def test_get_template_exact_match(self):
    """Test getting a template with an exact name match."""
    mock_templates = {
      "Template 1": {"category": "General", "systemprompt": "You are a helpful assistant.", "model": "gpt-4o"},
      "Template 2": {"category": "Code", "systemprompt": "You are a code assistant.", "model": "claude-3-5-sonnet"},
    }

    with patch("templates.load_template_data", return_value=mock_templates):
      result = get_template("Template 1", "dummy_path.json")

      assert result is not None
      key, template = result
      assert key == "Template 1"
      assert template["category"] == "General"
      assert template["model"] == "gpt-4o"

  def test_get_template_substring_match(self):
    """Test getting a template with a substring match."""
    mock_templates = {
      "Template Alpha": {"category": "General", "model": "gpt-4o"},
      "Template Beta": {"category": "Code", "model": "claude-3-5-sonnet"},
    }

    with patch("templates.load_template_data", return_value=mock_templates):
      result = get_template("Alpha", "dummy_path.json")

      assert result is not None
      key, template = result
      assert key == "Template Alpha"
      assert template["category"] == "General"

  def test_get_template_not_found(self):
    """Test getting a template that doesn't exist."""
    mock_templates = {"Template 1": {"category": "General"}}

    with patch("templates.load_template_data", return_value=mock_templates), pytest.raises(TemplateError, match="not found"):
      get_template("NonExistent", "dummy_path.json")

  def test_list_template_names(self):
    """Test listing template names."""
    mock_templates = {"Template 1": {"category": "General"}, "Template 2": {"category": "Code"}}

    with patch("templates.load_template_data", return_value=mock_templates), patch("sys.stdout.write") as mock_write:
      list_template_names("dummy_path.json")
      # Should have called write with template names
      assert mock_write.called

  def test_list_templates_all(self):
    """Test listing all templates."""
    mock_templates = {"Template 1": {"category": "General", "systemprompt": "You are helpful"}}

    with patch("templates.load_template_data", return_value=mock_templates), patch("sys.stdout.write") as mock_write:
      list_templates("dummy_path.json", "all")
      # Should have called write with template details
      assert mock_write.called

  def test_list_templates_specific(self):
    """Test listing a specific template."""
    mock_templates = {"Template 1": {"category": "General", "systemprompt": "You are helpful"}}

    with patch("templates.load_template_data", return_value=mock_templates), patch("sys.stdout.write") as mock_write:
      list_templates("dummy_path.json", "Template 1")
      # Should have called write with specific template details
      assert mock_write.called

  def test_load_template_data_caching(self):
    """Test that templates are cached and cache is invalidated on file change."""
    mock_templates = {"Template 1": {"category": "General"}}
    mock_json = json.dumps(mock_templates)

    # First load - should read from file
    with patch("os.path.exists", return_value=True), patch("os.path.getmtime", return_value=1234567890.0), patch(
      "builtins.open", mock_open(read_data=mock_json)
    ) as mock_file:
      result1 = load_template_data("test.json")
      assert mock_file.called
      assert "Template 1" in result1

    # Second load with same mtime - should use cache
    with patch("os.path.exists", return_value=True), patch("os.path.getmtime", return_value=1234567890.0), patch(
      "builtins.open", mock_open(read_data=mock_json)
    ) as mock_file:
      result2 = load_template_data("test.json")
      # File should not be opened again due to cache
      assert not mock_file.called
      assert result2 == result1

    # Third load with different mtime - should reload
    updated_templates = {"Template 1": {"category": "General"}, "Template 2": {"category": "Code"}}
    updated_json = json.dumps(updated_templates)

    with patch("os.path.exists", return_value=True), patch("os.path.getmtime", return_value=9999999999.0), patch(
      "builtins.open", mock_open(read_data=updated_json)
    ) as mock_file:
      result3 = load_template_data("test.json")
      assert mock_file.called
      assert "Template 2" in result3

  def test_load_template_data_force_reload(self):
    """Test force_reload bypasses cache."""
    mock_templates = {"Template 1": {"category": "General"}}
    mock_json = json.dumps(mock_templates)

    # First load
    with patch("os.path.exists", return_value=True), patch("os.path.getmtime", return_value=1234567890.0), patch(
      "builtins.open", mock_open(read_data=mock_json)
    ):
      load_template_data("test.json")

    # Force reload should read from file again
    with patch("os.path.exists", return_value=True), patch("os.path.getmtime", return_value=1234567890.0), patch(
      "builtins.open", mock_open(read_data=mock_json)
    ) as mock_file:
      load_template_data("test.json", force_reload=True)
      assert mock_file.called

  def test_get_template_case_insensitive(self):
    """Test case-insensitive template matching."""
    mock_templates = {"My Template": {"category": "General"}}

    with patch("templates.load_template_data", return_value=mock_templates):
      # Test lowercase
      result = get_template("my template", "dummy.json")
      assert result is not None
      key, _ = result
      assert key == "My Template"

  def test_get_template_normalized_match(self):
    """Test normalized template matching (matches on part before '-')."""
    mock_templates = {
      "Dejavu2 - Helpful AI": {"category": "General", "model": "gpt-4o"},
      "CodeHelper - Expert": {"category": "Code", "model": "claude-3-5-sonnet"},
    }

    with patch("templates.load_template_data", return_value=mock_templates):
      # Match by normalized key (part before '-', lowercased, no spaces)
      result = get_template("dejavu2", "dummy.json")
      assert result is not None
      key, template = result
      assert key == "Dejavu2 - Helpful AI"

      # Match by substring in normalized key
      result = get_template("code", "dummy.json")
      assert result is not None
      key, template = result
      assert key == "CodeHelper - Expert"

  def test_load_template_data_oserror(self):
    """Test handling of OSError when loading templates."""
    with patch("os.path.exists", return_value=True), patch("os.path.getmtime", side_effect=OSError("Permission denied")):
      with pytest.raises(ConfigurationError, match="Error reading template file"):
        load_template_data("permission_denied.json")


# fin
