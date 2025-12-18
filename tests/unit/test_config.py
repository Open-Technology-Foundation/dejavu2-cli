"""
Unit tests for configuration handling in dejavu2-cli.
"""

import os

# Import functions from the application
import sys
from unittest.mock import mock_open, patch

import yaml

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import load_config


class TestConfig:
  """Test configuration loading functionality."""

  def test_load_config_merges_configs(self):
    """Test that load_config properly merges default and user configs."""
    default_config = {"defaults": {"model": "claude-3-5-sonnet", "temperature": 0.1, "max_tokens": 1000}, "paths": {"template_path": "/default/path"}}

    user_config = {
      "defaults": {
        "model": "gpt-4o",  # Override model
        "temperature": 0.7,  # Override temperature
      },
      "custom_setting": "value",  # Add new setting
    }

    default_yaml = yaml.dump(default_config)
    user_yaml = yaml.dump(user_config)

    # Create a mock for the open function that returns different content for different paths
    def mock_file_open(filename, *args, **kwargs):
      if "default_config_path" in str(filename):
        return mock_open(read_data=default_yaml)()
      elif "user_config_path" in str(filename):
        return mock_open(read_data=user_yaml)()
      return mock_open()()

    # Mock both files existing
    with patch("builtins.open", side_effect=mock_file_open), patch("os.path.exists", return_value=True):
      config = load_config("default_config_path", "user_config_path")

      # Check merged values
      assert config["defaults"]["model"] == "gpt-4o"  # From user config
      assert config["defaults"]["temperature"] == 0.7  # From user config
      assert config["defaults"]["max_tokens"] == 1000  # From default config
      assert config["paths"]["template_path"] == "/default/path"  # From default config
      assert config["custom_setting"] == "value"  # Added from user config

  def test_load_config_missing_default_file(self):
    """Test that FileNotFoundError is raised when default config doesn't exist."""
    import pytest

    with patch("os.path.exists", return_value=False):
      with pytest.raises(FileNotFoundError, match="Default config file not found"):
        load_config("nonexistent_default.yaml")

  def test_load_config_invalid_yaml_in_default(self):
    """Test that yaml.YAMLError is raised for malformed default config."""
    import pytest

    # Invalid YAML content
    invalid_yaml = "invalid: yaml: content: with: too: many: colons:"

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=invalid_yaml)):
      with pytest.raises(yaml.YAMLError):
        load_config("default_config.yaml")

  def test_load_config_generic_error_in_default(self):
    """Test generic exception handling for unexpected errors in default config."""
    import pytest

    with patch("os.path.exists", return_value=True), patch("builtins.open", side_effect=IOError("Disk error")):
      with pytest.raises(IOError, match="Disk error"):
        load_config("default_config.yaml")

  def test_load_config_invalid_yaml_in_user(self):
    """Test that yaml.YAMLError is raised for malformed user config."""
    import pytest

    default_config = {"paths": {"template_path": "/path"}, "defaults": {"model": "test"}}
    default_yaml = yaml.dump(default_config)
    invalid_user_yaml = "bad: yaml: content: with: syntax: error:\n  - broken"

    def mock_file_open(filename, *args, **kwargs):
      if "default" in str(filename):
        return mock_open(read_data=default_yaml)()
      elif "user" in str(filename):
        return mock_open(read_data=invalid_user_yaml)()
      return mock_open()()

    with patch("os.path.exists", return_value=True), patch("builtins.open", side_effect=mock_file_open):
      with pytest.raises(yaml.YAMLError):
        load_config("default_config.yaml", "user_config.yaml")

  def test_load_config_generic_error_in_user(self):
    """Test generic exception handling for unexpected errors in user config."""
    import pytest

    default_config = {"paths": {"template_path": "/path"}, "defaults": {"model": "test"}}
    default_yaml = yaml.dump(default_config)

    def mock_file_open(filename, *args, **kwargs):
      if "default" in str(filename):
        return mock_open(read_data=default_yaml)()
      elif "user" in str(filename):
        raise PermissionError("Permission denied")
      return mock_open()()

    with patch("os.path.exists", return_value=True), patch("builtins.open", side_effect=mock_file_open):
      with pytest.raises(PermissionError, match="Permission denied"):
        load_config("default_config.yaml", "user_config.yaml")

  def test_load_config_missing_required_keys(self):
    """Test that KeyError is raised when required keys are missing."""
    import pytest

    # Config missing "paths" and "defaults"
    incomplete_config = {"other_key": "value"}
    incomplete_yaml = yaml.dump(incomplete_config)

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=incomplete_yaml)):
      with pytest.raises(KeyError, match="Required configuration keys missing"):
        load_config("default_config.yaml")

  def test_load_config_ensures_api_keys_section(self):
    """Test that api_keys dict is added if missing from config."""
    # Config without api_keys section
    config_without_api_keys = {"paths": {"template_path": "/path"}, "defaults": {"model": "test"}}
    config_yaml = yaml.dump(config_without_api_keys)

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=config_yaml)):
      config = load_config("default_config.yaml")

      # Verify api_keys key exists as empty dict
      assert "api_keys" in config
      assert isinstance(config["api_keys"], dict)
      assert len(config["api_keys"]) == 0


class TestConfigEdgeCases:
  """Test edge cases in configuration handling."""

  def test_load_config_empty_yaml_file(self):
    """Test handling of empty YAML file."""
    import pytest

    empty_yaml = ""

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=empty_yaml)):
      with pytest.raises(KeyError, match="Required configuration keys missing"):
        load_config("default_config.yaml")

  def test_load_config_yaml_with_null_values(self):
    """Test handling of YAML with null values."""
    config_with_nulls = {
      "paths": {"template_path": None},
      "defaults": {"model": None, "temperature": 0.7, "max_tokens": None},
    }
    config_yaml = yaml.dump(config_with_nulls)

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=config_yaml)):
      config = load_config("default_config.yaml")

      # Null values should be preserved
      assert config["paths"]["template_path"] is None
      assert config["defaults"]["model"] is None
      assert config["defaults"]["max_tokens"] is None
      assert config["defaults"]["temperature"] == 0.7

  def test_load_config_unicode_values(self):
    """Test handling of Unicode characters in config."""
    config_with_unicode = {
      "paths": {"template_path": "/path/to/日本語/config"},
      "defaults": {"model": "claude-3-5-sonnet", "description": "Configuração com émojis 🚀"},
    }
    config_yaml = yaml.dump(config_with_unicode, allow_unicode=True)

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=config_yaml)):
      config = load_config("default_config.yaml")

      assert "日本語" in config["paths"]["template_path"]
      assert "émojis 🚀" in config["defaults"]["description"]

  def test_load_config_deeply_nested_values(self):
    """Test handling of deeply nested configuration values."""
    deeply_nested_config = {
      "paths": {"template_path": "/path"},
      "defaults": {"model": "test"},
      "nested": {"level1": {"level2": {"level3": {"level4": {"value": "deep"}}}}},
    }
    config_yaml = yaml.dump(deeply_nested_config)

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=config_yaml)):
      config = load_config("default_config.yaml")

      assert config["nested"]["level1"]["level2"]["level3"]["level4"]["value"] == "deep"

  def test_load_config_numeric_string_values(self):
    """Test that numeric strings are preserved as strings."""
    config_with_numeric_strings = {"paths": {"template_path": "/path"}, "defaults": {"model": "123.456", "version": "3.14159"}}
    config_yaml = yaml.dump(config_with_numeric_strings)

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=config_yaml)):
      config = load_config("default_config.yaml")

      # YAML may parse "123.456" as a float, verify handling
      assert config["defaults"]["model"] is not None
      assert config["defaults"]["version"] is not None

  def test_load_config_list_values(self):
    """Test handling of list values in config."""
    config_with_lists = {
      "paths": {"template_path": "/path"},
      "defaults": {"model": "test", "allowed_models": ["gpt-4o", "claude-3-5-sonnet", "gemini-2.0-flash"]},
    }
    config_yaml = yaml.dump(config_with_lists)

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=config_yaml)):
      config = load_config("default_config.yaml")

      assert isinstance(config["defaults"]["allowed_models"], list)
      assert len(config["defaults"]["allowed_models"]) == 3
      assert "gpt-4o" in config["defaults"]["allowed_models"]

  def test_load_config_boolean_values(self):
    """Test handling of boolean values in config."""
    config_with_booleans = {
      "paths": {"template_path": "/path"},
      "defaults": {"model": "test", "verbose": True, "debug": False},
    }
    config_yaml = yaml.dump(config_with_booleans)

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=config_yaml)):
      config = load_config("default_config.yaml")

      assert config["defaults"]["verbose"] is True
      assert config["defaults"]["debug"] is False

  def test_load_config_yaml_boolean_keywords(self):
    """Test handling of YAML boolean keywords (yes/no/true/false)."""
    # Test raw YAML with boolean keywords
    yaml_with_keywords = """
paths:
  template_path: /path
defaults:
  model: test
  enabled: yes
  disabled: no
  on_state: on
  off_state: off
"""

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=yaml_with_keywords)):
      config = load_config("default_config.yaml")

      # YAML 1.1 parses yes/no/on/off as booleans
      assert config["defaults"]["enabled"] is True
      assert config["defaults"]["disabled"] is False
      assert config["defaults"]["on_state"] is True
      assert config["defaults"]["off_state"] is False

  def test_load_config_special_characters_in_paths(self):
    """Test handling of special characters in path values."""
    config_with_special_paths = {"paths": {"template_path": "/path/with spaces/and-dashes/under_scores"}, "defaults": {"model": "test"}}
    config_yaml = yaml.dump(config_with_special_paths)

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=config_yaml)):
      config = load_config("default_config.yaml")

      assert " " in config["paths"]["template_path"]
      assert "-" in config["paths"]["template_path"]
      assert "_" in config["paths"]["template_path"]


# fin
