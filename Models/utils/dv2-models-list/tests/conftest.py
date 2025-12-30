"""
Pytest fixtures for dv2-models-list test suite.
"""

import json
import pathlib
import tempfile
from typing import Any

import pytest


@pytest.fixture
def sample_models() -> dict[str, Any]:
  """Sample model data for testing."""
  return {
    "gpt-4o": {
      "model": "gpt-4o",
      "alias": "4o",
      "parent": "OpenAI",
      "family": "gpt4",
      "model_category": "LLM",
      "available": 9,
      "enabled": 9,
      "vision": 1,
      "context_window": 128000,
      "max_output_tokens": 16384,
      "token_costs": "$2.50/$10.00",
    },
    "claude-sonnet-4-20250514": {
      "model": "claude-sonnet-4-20250514",
      "alias": "sonnet",
      "parent": "Anthropic",
      "family": "claude4",
      "model_category": "LLM",
      "available": 9,
      "enabled": 9,
      "vision": 1,
      "context_window": 200000,
      "max_output_tokens": 8192,
      "token_costs": "$3.00/$15.00",
    },
    "gemini-2.0-flash": {
      "model": "gemini-2.0-flash",
      "alias": "flash",
      "parent": "Google",
      "family": "gemini2",
      "model_category": "LLM",
      "available": 8,
      "enabled": 7,
      "vision": 1,
      "context_window": 1000000,
      "max_output_tokens": 8192,
      "token_costs": "$0.10/$0.40",
    },
    "text-embedding-3-small": {
      "model": "text-embedding-3-small",
      "alias": "embed-small",
      "parent": "OpenAI",
      "family": "embed",
      "model_category": "embed",
      "available": 9,
      "enabled": 5,
      "vision": 0,
      "context_window": 8191,
      "max_output_tokens": 0,
      "token_costs": "$0.02/M",
    },
    "disabled-model": {
      "model": "disabled-model",
      "alias": "disabled",
      "parent": "TestProvider",
      "family": "test",
      "model_category": "LLM",
      "available": 0,
      "enabled": 0,
      "vision": 0,
      "context_window": 4096,
      "max_output_tokens": 1024,
      "token_costs": "$0.00/$0.00",
    },
  }


@pytest.fixture
def sample_model_data() -> dict[str, Any]:
  """Single model data for filter testing."""
  return {
    "model": "gpt-4o",
    "alias": "4o",
    "parent": "OpenAI",
    "family": "gpt4",
    "model_category": "LLM",
    "available": 9,
    "enabled": 9,
    "vision": 1,
    "context_window": 128000,
    "max_output_tokens": 16384,
    "token_costs": "$2.50/$10.00",
    "nested": {
      "field": "value",
      "number": 42,
    },
  }


@pytest.fixture
def temp_models_file(sample_models: dict[str, Any]) -> pathlib.Path:
  """Create a temporary Models.json file."""
  with tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".json",
    delete=False,
    encoding="utf-8",
  ) as f:
    json.dump(sample_models, f, indent=2)
    return pathlib.Path(f.name)


@pytest.fixture
def temp_invalid_json_file() -> pathlib.Path:
  """Create a temporary file with invalid JSON."""
  with tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".json",
    delete=False,
    encoding="utf-8",
  ) as f:
    f.write("{invalid json content")
    return pathlib.Path(f.name)


@pytest.fixture
def temp_empty_models_file() -> pathlib.Path:
  """Create a temporary empty Models.json file."""
  with tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".json",
    delete=False,
    encoding="utf-8",
  ) as f:
    json.dump({}, f)
    return pathlib.Path(f.name)


@pytest.fixture
def nonexistent_path() -> pathlib.Path:
  """Return a path that doesn't exist."""
  return pathlib.Path("/nonexistent/path/to/Models.json")


# fin
