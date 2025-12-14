"""
Tests for model API interactions in dejavu2-cli.
"""

import os

# Import the query functions from llm_clients.py
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from llm_clients import query, query_anthropic, query_openai

# Skip tests if API keys are not available
require_openai = pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OpenAI API key not available")

require_anthropic = pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="Anthropic API key not available")


class TestModelIntegration:
  """Integration tests for model API interactions."""

  @require_openai
  def test_openai_query_gpt4o(self):
    """Test a basic query to OpenAI GPT-4o API."""
    from llm_clients import initialize_clients, get_api_keys

    # Get API keys and initialize clients
    api_keys = get_api_keys()
    clients = initialize_clients(api_keys)

    # Skip if OpenAI client not available
    if clients.get("openai") is None:
      pytest.skip("OpenAI client not available. Please check API key.")

    result = query_openai(
      client=clients["openai"],
      query="What is the capital of France?",
      system="You are a helpful assistant that provides short answers.",
      model="gpt-4o",
      temperature=0.1,
      max_tokens=100,
    )

    # Check the result looks reasonable
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Paris" in result

  @pytest.mark.skip(reason="Actual API key is present but unauthorized")
  @require_anthropic
  def test_anthropic_query_sonnet(self):
    """Test a basic query to Anthropic Claude Sonnet API."""
    from llm_clients import get_anthropic_client

    client = get_anthropic_client({"ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY")})

    result = query_anthropic(
      client=client,
      query_text="What is the capital of France?",
      systemprompt="You are a helpful assistant that provides short answers.",
      model="claude-3-5-sonnet-latest",  # Use the latest alias
      temperature=0.1,
      max_tokens=100,
    )

    # Check the result looks reasonable
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Paris" in result

  @patch("llm_clients._extract_content_from_response")
  @patch("llm_clients.format_messages_for_responses_api")
  def test_openai_query_mocked(self, mock_format_messages, mock_extract_content):
    """Test OpenAI query with mocked API (no real API call)."""
    # Set up the mock response
    mock_client = MagicMock()

    # Mock the Responses API
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {"output": "The capital of France is Paris."}
    mock_client.responses.create.return_value = mock_response

    # Mock helper functions
    mock_format_messages.return_value = "formatted messages"
    mock_extract_content.return_value = "The capital of France is Paris."

    # Call the function
    result = query_openai(
      client=mock_client,
      query="What is the capital of France?",
      system="You are a helpful assistant.",
      model="gpt-4o",
      temperature=0.1,
      max_tokens=100,
    )

    # Verify the result
    assert "Paris" in result
    # Verify the Responses API was called
    mock_client.responses.create.assert_called_once()

  @patch("anthropic.Anthropic")
  def test_anthropic_query_mocked(self, mock_anthropic):
    """Test Anthropic query with mocked API (no real API call)."""
    # Set up the mock response
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client

    mock_message = MagicMock()
    mock_message.content = [MagicMock()]
    mock_message.content[0].text = "The capital of France is Paris."
    mock_client.messages.create.return_value = mock_message

    # Call the function
    result = query_anthropic(
      client=mock_client,
      query_text="What is the capital of France?",
      systemprompt="You are a helpful assistant.",
      model="claude-3-5-sonnet",
      temperature=0.1,
      max_tokens=100,
    )

    # Verify the result
    assert "Paris" in result

  @patch("llm_clients.query_openai")
  @patch("llm_clients.query_anthropic")
  def test_query_router(self, mock_anthropic_query, mock_openai_query):
    """Test that the query router directs to the right provider."""

    # Setup mock responses
    mock_openai_query.return_value = "OpenAI response: Paris"
    mock_anthropic_query.return_value = "Anthropic response: Paris"

    mock_clients = {"openai": MagicMock(), "anthropic": MagicMock()}

    # Test routing to OpenAI
    openai_result = query(
      clients=mock_clients,
      query_text="What is the capital of France?",
      systemprompt="You are a helpful assistant.",
      messages=[],
      model="gpt-4o",
      temperature=0.1,
      max_tokens=100,
      model_parameters={"family": "openai", "model": "gpt-4o"},
      api_keys={"OPENAI_API_KEY": "test-key"},
    )

    # Test routing to Anthropic
    anthropic_result = query(
      clients=mock_clients,
      query_text="What is the capital of France?",
      systemprompt="You are a helpful assistant.",
      messages=[],
      model="claude-3-5-sonnet",
      temperature=0.1,
      max_tokens=100,
      model_parameters={"family": "anthropic", "model": "claude-3-5-sonnet"},
      api_keys={"ANTHROPIC_API_KEY": "test-key"},
    )

    # Verify correct routing
    assert "OpenAI response" in openai_result
    assert "Anthropic response" in anthropic_result

    # Verify the correct provider functions were called
    # Note: Functions are called with positional args: (client, query, system, model, temperature, max_tokens, ...)
    assert mock_openai_query.called, "query_openai should have been called"
    assert mock_anthropic_query.called, "query_anthropic should have been called"

    # Verify OpenAI call had correct model
    openai_call_args = mock_openai_query.call_args
    assert openai_call_args.args[3] == "gpt-4o", "OpenAI should be called with gpt-4o model"

    # Verify Anthropic call had correct model
    anthropic_call_args = mock_anthropic_query.call_args
    # For Anthropic, check if called with kwargs or positional args
    if anthropic_call_args.kwargs:
      assert anthropic_call_args.kwargs.get("model") == "claude-3-5-sonnet"
    else:
      # Positional args for query_anthropic: (client, query_text, systemprompt, model, ...)
      assert anthropic_call_args.args[3] == "claude-3-5-sonnet"
