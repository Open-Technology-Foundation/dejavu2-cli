"""
Unit tests for model handling in dejavu2-cli.
"""

import json
import os

# Import functions from the application
import sys
from unittest.mock import mock_open, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from errors import ConfigurationError, ModelError
from models import get_canonical_model, list_available_canonical_models


class TestModels:
  """Test model handling and selection functionality."""

  def test_list_available_canonical_models(self):
    """Test listing available models from a mock JSON file."""
    mock_models = {
      "gpt-4o": {"model": "gpt-4o", "parent": "openai", "available": 1, "enabled": 1},
      "claude-3-5-sonnet": {"model": "claude-3-5-sonnet", "parent": "anthropic", "available": 1, "enabled": 1},
      "unavailable-model": {"model": "unavailable-model", "parent": "test", "available": 0, "enabled": 1},
    }

    mock_json = json.dumps(mock_models)

    with patch("builtins.open", mock_open(read_data=mock_json)):
      models = list_available_canonical_models("dummy_path.json")

      # Check models list - only available models should be included
      assert "gpt-4o" in models
      assert "claude-3-5-sonnet" in models
      assert "unavailable-model" not in models
      assert len(models) == 2

  def test_list_available_canonical_models_file_not_found(self):
    """Test listing models when the JSON file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError), pytest.raises(ConfigurationError, match="Models file not found"):
      list_available_canonical_models("nonexistent.json")

  def test_list_available_canonical_models_invalid_json(self):
    """Test listing models with invalid JSON content."""
    with patch("builtins.open", mock_open(read_data='{"invalid": json')):
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

    with patch("builtins.open", mock_open(read_data=mock_json)):
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

    with patch("builtins.open", mock_open(read_data=mock_json)):
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

    with patch("builtins.open", mock_open(read_data=mock_json)), pytest.raises(ModelError, match="Model 'nonexistent-model' not found"):
      get_canonical_model("nonexistent-model", "dummy_path.json")

  def test_get_canonical_model_file_not_found(self):
    """Test getting canonical model when models file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError), pytest.raises(ConfigurationError, match="Models file not found"):
      get_canonical_model("gpt-4o", "nonexistent.json")

  def test_get_canonical_model_invalid_json(self):
    """Test getting canonical model with invalid JSON."""
    with patch("builtins.open", mock_open(read_data='{"invalid": json')):
      with pytest.raises(ConfigurationError, match="Invalid JSON in models file"):
        get_canonical_model("gpt-4o", "invalid.json")


# fin
