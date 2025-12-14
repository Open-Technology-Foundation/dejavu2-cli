"""
Unit tests for display functions in dejavu2-cli.
"""

import io
import os
import sys
from unittest.mock import patch

# Import functions from the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from display import display_status


class TestDisplay:
  """Test display formatting and output functions."""

  @patch("sys.stdout", new_callable=io.StringIO)
  def test_display_status(self, mock_stdout):
    """Test displaying status information."""
    config = {"defaults": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000}}

    model_parameters = {
      "family": "openai",
      "model": "gpt-4o",
      "temperature": 0.5,
      "max_tokens": 1000,
      "max_output_tokens": 1000,
      "context_window": 128000,
      "systemprompt": "You are a test assistant.",
    }

    kwargs = {
      "model": "gpt-4o",
      "temperature": 0.5,
      "max_tokens": 1000,
      "systemprompt": "You are a test assistant.",
      "template": "test_template",
      "reference": ["test.txt"],
      "knowledgebase": "test_kb",
      "knowledgebase_query": "test query",
    }

    query_texts = ["Test query"]

    # Call display_status
    display_status(
      kwargs=kwargs, query_texts=query_texts, config=config, model_parameters=model_parameters, print_full_systemprompt=True, conversation=None
    )

    # Get the captured output
    output = mock_stdout.getvalue()

    # Check that the output contains expected section headers
    assert "=== CONFIGURATION ===" in output
    assert "=== MODEL INFORMATION ===" in output
    assert "=== QUERY PARAMETERS ===" in output
    assert "=== QUERY CONTENT ===" in output

    # Check specific configuration fields
    assert "Template: test_template" in output

    # Check specific model information fields
    assert "Selected Model/Alias: gpt-4o" in output
    assert "Canonical Model: gpt-4o" in output
    assert "Family: openai" in output
    assert "Context Window: 128000" in output
    assert "Max Output Tokens: 1000" in output

    # Check query parameters
    assert "Temperature: 0.5" in output
    assert "Max Tokens: 1000" in output
    assert "Reference Files: ['test.txt']" in output
    assert "Knowledgebase: test_kb" in output

    # Check query content
    assert "System Prompt:" in output
    assert "You are a test assistant" in output
    assert "Query:" in output
    assert "Test query" in output

  @patch("sys.stdout", new_callable=io.StringIO)
  def test_display_status_openai_api_key_present(self, mock_stdout):
    """Test OpenAI API status display when key is present."""
    config = {"defaults": {"model": "gpt-4o"}}

    model_parameters = {
      "family": "openai",
      "model": "gpt-4o",
      "apikey": "OPENAI_API_KEY",
      "api_key_valid": True,
      "max_output_tokens": 1000,
      "context_window": 128000,
    }

    kwargs = {"model": "gpt-4o", "temperature": 0.5, "max_tokens": 1000, "systemprompt": "Test", "template": "test", "reference": [], "knowledgebase": None}

    display_status(kwargs=kwargs, query_texts=["test"], config=config, model_parameters=model_parameters, print_full_systemprompt=False, conversation=None)

    output = mock_stdout.getvalue()
    assert "=== API STATUS ===" in output
    assert "OpenAI API: Key Present" in output

  @patch("sys.stdout", new_callable=io.StringIO)
  def test_display_status_openai_api_key_missing(self, mock_stdout):
    """Test OpenAI API status display when key is missing."""
    config = {"defaults": {"model": "gpt-4o"}}

    model_parameters = {
      "family": "openai",
      "model": "gpt-4o",
      "apikey": "OPENAI_API_KEY",
      "api_key_valid": False,
      "max_output_tokens": 1000,
      "context_window": 128000,
    }

    kwargs = {"model": "gpt-4o", "temperature": 0.5, "max_tokens": 1000, "systemprompt": "Test", "template": "test", "reference": [], "knowledgebase": None}

    display_status(kwargs=kwargs, query_texts=["test"], config=config, model_parameters=model_parameters, print_full_systemprompt=False, conversation=None)

    output = mock_stdout.getvalue()
    assert "OpenAI API: Key Missing" in output

  @patch("sys.stdout", new_callable=io.StringIO)
  def test_display_status_anthropic_api_key(self, mock_stdout):
    """Test Anthropic API status display."""
    config = {"defaults": {"model": "claude-4"}}

    model_parameters = {
      "family": "anthropic",
      "model": "claude-sonnet-4",
      "apikey": "ANTHROPIC_API_KEY",
      "api_key_valid": True,
      "max_output_tokens": 8192,
      "context_window": 200000,
    }

    kwargs = {"model": "claude-4", "temperature": 0.5, "max_tokens": 1000, "systemprompt": "Test", "template": "test", "reference": [], "knowledgebase": None}

    display_status(kwargs=kwargs, query_texts=["test"], config=config, model_parameters=model_parameters, print_full_systemprompt=False, conversation=None)

    output = mock_stdout.getvalue()
    assert "Anthropic API: Key Present" in output

  @patch("sys.stdout", new_callable=io.StringIO)
  def test_display_status_google_api_key(self, mock_stdout):
    """Test Google API status display."""
    config = {"defaults": {"model": "gemini-2.0"}}

    model_parameters = {
      "family": "google",
      "model": "gemini-2.0-flash",
      "apikey": "GOOGLE_API_KEY",
      "api_key_valid": True,
      "max_output_tokens": 8192,
      "context_window": 1000000,
    }

    kwargs = {"model": "gemini-2.0", "temperature": 0.5, "max_tokens": 1000, "systemprompt": "Test", "template": "test", "reference": [], "knowledgebase": None}

    display_status(kwargs=kwargs, query_texts=["test"], config=config, model_parameters=model_parameters, print_full_systemprompt=False, conversation=None)

    output = mock_stdout.getvalue()
    assert "Google API: Key Present" in output

  @patch("sys.stdout", new_callable=io.StringIO)
  def test_display_status_with_config_file(self, mock_stdout):
    """Test config file path display when present."""
    config = {"defaults": {"model": "gpt-4o"}, "config_file": "/home/user/.config/dejavu2-cli/config.yaml"}

    model_parameters = {"family": "openai", "model": "gpt-4o", "max_output_tokens": 1000, "context_window": 128000}

    kwargs = {"model": "gpt-4o", "temperature": 0.5, "max_tokens": 1000, "systemprompt": "Test", "template": "test", "reference": [], "knowledgebase": None}

    display_status(kwargs=kwargs, query_texts=["test"], config=config, model_parameters=model_parameters, print_full_systemprompt=False, conversation=None)

    output = mock_stdout.getvalue()
    assert "Config File:" in output
    assert "/home/user/.config/dejavu2-cli/config.yaml" in output

  @patch("sys.stdout", new_callable=io.StringIO)
  def test_display_status_long_systemprompt_truncation(self, mock_stdout):
    """Test truncation logic for long prompts (>10 lines)."""
    config = {"defaults": {"model": "gpt-4o"}}
    model_parameters = {"family": "openai", "model": "gpt-4o", "max_output_tokens": 1000, "context_window": 128000}

    # Create a system prompt with 20 lines
    long_prompt = "\n".join([f"Line {i}" for i in range(1, 21)])

    kwargs = {"model": "gpt-4o", "temperature": 0.5, "max_tokens": 1000, "systemprompt": long_prompt, "template": "test", "reference": [], "knowledgebase": None}

    display_status(kwargs=kwargs, query_texts=["test"], config=config, model_parameters=model_parameters, print_full_systemprompt=False, conversation=None)

    output = mock_stdout.getvalue()

    # Should show truncation message
    assert "lines hidden" in output or "Use --print-systemprompt" in output
    # Should show first 3 lines
    assert "Line 1" in output
    assert "Line 2" in output
    assert "Line 3" in output
    # Should show last 3 lines
    assert "Line 18" in output
    assert "Line 19" in output
    assert "Line 20" in output

  @patch("sys.stdout", new_callable=io.StringIO)
  def test_display_status_long_query_truncation(self, mock_stdout):
    """Test truncation for queries >500 chars."""
    config = {"defaults": {"model": "gpt-4o"}}
    model_parameters = {"family": "openai", "model": "gpt-4o", "max_output_tokens": 1000, "context_window": 128000}

    # Create a query with 600 characters
    long_query = "A" * 600

    kwargs = {"model": "gpt-4o", "temperature": 0.5, "max_tokens": 1000, "systemprompt": "Test", "template": "test", "reference": [], "knowledgebase": None}

    display_status(kwargs=kwargs, query_texts=[long_query], config=config, model_parameters=model_parameters, print_full_systemprompt=False, conversation=None)

    output = mock_stdout.getvalue()

    # Should show truncation
    assert "truncated" in output or "..." in output
    # Should mention character count
    assert "600" in output or "chars" in output
