"""
Unit tests for model handling in dejavu2-cli.
"""

import json
import os
import sys
from unittest.mock import mock_open, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from errors import ConfigurationError, ModelError
from models import get_canonical_model, list_available_canonical_models, load_models_json


class TestModels:
  """Test model handling and selection functionality."""

  def setup_method(self):
    """Clear module-level cache before each test."""
    import models

    models._models_cache.clear()
    models._cache_mtime.clear()

  def test_list_available_canonical_models(self):
    """Test listing available models from a mock JSON file."""
    mock_models = {
      "gpt-4o": {"model": "gpt-4o", "parent": "openai", "available": 1, "enabled": 1},
      "claude-3-5-sonnet": {"model": "claude-3-5-sonnet", "parent": "anthropic", "available": 1, "enabled": 1},
      "unavailable-model": {"model": "unavailable-model", "parent": "test", "available": 0, "enabled": 1},
    }

    mock_json = json.dumps(mock_models)

    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)):
      models = list_available_canonical_models("dummy_path.json")

      # Check models list - only available models should be included
      assert "gpt-4o" in models
      assert "claude-3-5-sonnet" in models
      assert "unavailable-model" not in models
      assert len(models) == 2

  def test_list_available_canonical_models_file_not_found(self):
    """Test listing models when the JSON file doesn't exist."""
    with patch("os.path.getmtime", side_effect=FileNotFoundError), pytest.raises(ConfigurationError, match="Models file not found"):
      list_available_canonical_models("nonexistent.json")

  def test_list_available_canonical_models_invalid_json(self):
    """Test listing models with invalid JSON content."""
    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data='{"invalid": json')):
      with pytest.raises(ConfigurationError, match="Invalid JSON in models file"):
        list_available_canonical_models("invalid.json")

  def test_get_canonical_model_exact_match(self):
    """Test getting canonical model with an exact match."""
    mock_models = {
      "gpt-4o": {
        "model": "gpt-4o",
        "series": "gpt",
        "url": "https://api.openai.com",
        "apikey": "OPENAI_API_KEY",
        "context_window": 128000,
        "max_output_tokens": 4096,
        "parent": "openai",
        "available": 1,
        "enabled": 1,
      }
    }

    mock_json = json.dumps(mock_models)

    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)):
      canonical_name, model_info = get_canonical_model("gpt-4o", "dummy_path.json")

      assert canonical_name == "gpt-4o"
      assert model_info is not None
      assert model_info["parent"] == "openai"
      assert model_info["model"] == "gpt-4o"

  def test_get_canonical_model_alias(self):
    """Test getting canonical model with an alias."""
    mock_models = {
      "gpt-4o": {
        "model": "gpt-4o",
        "series": "gpt",
        "url": "https://api.openai.com",
        "apikey": "OPENAI_API_KEY",
        "context_window": 128000,
        "max_output_tokens": 4096,
        "parent": "openai",
        "alias": "gpt4",
        "available": 1,
        "enabled": 1,
      }
    }

    mock_json = json.dumps(mock_models)

    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)):
      canonical_name, model_info = get_canonical_model("gpt4", "dummy_path.json")

      assert canonical_name == "gpt-4o"
      assert model_info is not None
      assert model_info["parent"] == "openai"
      assert model_info["model"] == "gpt-4o"

  def test_get_canonical_model_not_found(self):
    """Test getting canonical model when not found."""
    mock_models = {
      "gpt-4o": {
        "model": "gpt-4o",
        "series": "gpt",
        "url": "https://api.openai.com",
        "apikey": "OPENAI_API_KEY",
        "context_window": 128000,
        "max_output_tokens": 4096,
        "parent": "openai",
        "available": 1,
        "enabled": 1,
      }
    }

    mock_json = json.dumps(mock_models)

    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)), pytest.raises(
      ModelError, match="Model 'nonexistent-model' not found"
    ):
      get_canonical_model("nonexistent-model", "dummy_path.json")

  def test_get_canonical_model_file_not_found(self):
    """Test getting canonical model when models file doesn't exist."""
    with patch("os.path.getmtime", side_effect=FileNotFoundError), pytest.raises(ConfigurationError, match="Models file not found"):
      get_canonical_model("gpt-4o", "nonexistent.json")

  def test_get_canonical_model_invalid_json(self):
    """Test getting canonical model with invalid JSON."""
    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data='{"invalid": json')):
      with pytest.raises(ConfigurationError, match="Invalid JSON in models file"):
        get_canonical_model("gpt-4o", "invalid.json")

  def test_load_models_json_caching(self):
    """Test that models are cached and cache is invalidated on file change."""
    mock_models = {"gpt-4o": {"model": "gpt-4o", "parent": "openai", "available": 1}}
    mock_json = json.dumps(mock_models)

    # First load - should read from file
    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)) as mock_file:
      result1 = load_models_json("test.json")
      assert mock_file.called
      assert "gpt-4o" in result1

    # Second load with same mtime - should use cache
    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)) as mock_file:
      result2 = load_models_json("test.json")
      # File should not be opened again due to cache
      assert not mock_file.called
      assert result2 == result1

    # Third load with different mtime - should reload
    updated_models = {"gpt-4o": {"model": "gpt-4o", "parent": "openai", "available": 1}, "new-model": {"model": "new-model", "parent": "test", "available": 1}}
    updated_json = json.dumps(updated_models)

    with patch("os.path.getmtime", return_value=9999999999.0), patch("builtins.open", mock_open(read_data=updated_json)) as mock_file:
      result3 = load_models_json("test.json")
      assert mock_file.called
      assert "new-model" in result3

  def test_load_models_json_force_reload(self):
    """Test force_reload bypasses cache."""
    mock_models = {"gpt-4o": {"model": "gpt-4o", "parent": "openai", "available": 1}}
    mock_json = json.dumps(mock_models)

    # First load
    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)):
      load_models_json("test.json")

    # Force reload should read from file again
    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)) as mock_file:
      load_models_json("test.json", force_reload=True)
      assert mock_file.called

  def test_get_canonical_model_case_insensitive_alias(self):
    """Test that alias matching is case-insensitive."""
    mock_models = {
      "claude-3-5-sonnet-latest": {
        "model": "claude-3-5-sonnet-latest",
        "alias": "sonnet",
        "parent": "anthropic",
        "available": 1,
        "enabled": 1,
      }
    }
    mock_json = json.dumps(mock_models)

    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)):
      # Test lowercase
      canonical_name, _ = get_canonical_model("sonnet", "dummy.json")
      assert canonical_name == "claude-3-5-sonnet-latest"

  def test_list_models_with_mixed_availability(self):
    """Test listing models with various availability values."""
    mock_models = {
      "model-available-1": {"model": "model-available-1", "available": 1},
      "model-available-9": {"model": "model-available-9", "available": 9},
      "model-unavailable-0": {"model": "model-unavailable-0", "available": 0},
      "model-no-field": {"model": "model-no-field"},  # No available field
    }
    mock_json = json.dumps(mock_models)

    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)):
      models = list_available_canonical_models("dummy.json")

      assert "model-available-1" in models
      assert "model-available-9" in models
      assert "model-unavailable-0" not in models
      # Models without 'available' field should be included (None != 0)
      assert "model-no-field" in models

  def test_get_canonical_model_with_alias(self):
    """Test model alias lookup."""
    mock_models = {
      "gpt-4o-2024-11-20": {
        "model": "gpt-4o-2024-11-20",
        "alias": "gpt4o",
        "parent": "openai",
        "available": 1,
        "enabled": 1,
      },
      "claude-3-5-sonnet-latest": {
        "model": "claude-3-5-sonnet-latest",
        "alias": "sonnet",
        "parent": "anthropic",
        "available": 1,
        "enabled": 1,
      },
    }
    mock_json = json.dumps(mock_models)

    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)):
      # Test OpenAI alias
      canonical_name, model_info = get_canonical_model("gpt4o", "dummy.json")
      assert canonical_name == "gpt-4o-2024-11-20"
      assert model_info["parent"] == "openai"

      # Clear cache for next test
      import models

      models._models_cache.clear()
      models._cache_mtime.clear()

    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)):
      # Test Anthropic alias
      canonical_name, model_info = get_canonical_model("sonnet", "dummy.json")
      assert canonical_name == "claude-3-5-sonnet-latest"
      assert model_info["parent"] == "anthropic"

  def test_get_canonical_model_alias_unavailable(self):
    """Test that unavailable models via alias return None."""
    mock_models = {
      "old-model": {
        "model": "old-model",
        "alias": "old",
        "parent": "test",
        "available": 0,
        "enabled": 1,
      }
    }
    mock_json = json.dumps(mock_models)

    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)):
      canonical_name, model_info = get_canonical_model("old", "dummy.json")
      assert canonical_name is None
      assert model_info == {}

  def test_get_canonical_model_alias_disabled(self):
    """Test that disabled models via alias return None."""
    mock_models = {
      "disabled-model": {
        "model": "disabled-model",
        "alias": "disabled",
        "parent": "test",
        "available": 1,
        "enabled": 0,
      }
    }
    mock_json = json.dumps(mock_models)

    with patch("os.path.getmtime", return_value=1234567890.0), patch("builtins.open", mock_open(read_data=mock_json)):
      canonical_name, model_info = get_canonical_model("disabled", "dummy.json")
      assert canonical_name is None
      assert model_info == {}


# fin
