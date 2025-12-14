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
