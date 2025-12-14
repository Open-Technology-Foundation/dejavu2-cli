"""
Unit tests for LLM client functionality in dejavu2-cli.

Tests all enabled LLM providers: OpenAI, Anthropic, Google/Gemini, and Ollama.
"""

import os

# Import functions from the application
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from llm_clients import (
  _extract_content_from_response,
  _is_reasoning_model,
  _supports_image_generation,
  _supports_vision,
  _supports_web_search,
  format_messages_for_responses_api,
  get_api_keys,
  initialize_clients,
  query,
  query_anthropic,
  query_gemini,
  query_llama,
  query_openai,
)


class TestLLMClients:
  """Test LLM client functionality for all enabled providers."""

  def test_get_api_keys(self):
    """Test getting API keys from environment."""
    with patch.dict(
      os.environ,
      {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "GOOGLE_API_KEY": "test-google-key",
        "OLLAMA_API_KEY": "test-ollama-key",
      },
    ):
      keys = get_api_keys()

      assert keys["OPENAI_API_KEY"] == "test-openai-key"
      assert keys["ANTHROPIC_API_KEY"] == "test-anthropic-key"
      assert keys["GOOGLE_API_KEY"] == "test-google-key"
      assert keys["OLLAMA_API_KEY"] == "test-ollama-key"

  def test_get_api_keys_missing(self):
    """Test getting API keys when some are missing."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"}, clear=True):
      keys = get_api_keys()

      assert keys["OPENAI_API_KEY"] == "test-openai-key"
      assert keys["ANTHROPIC_API_KEY"] == ""
      assert keys["GOOGLE_API_KEY"] == ""
      assert keys["OLLAMA_API_KEY"] == "llama"  # Default value

  def test_initialize_clients(self):
    """Test initializing all LLM clients."""
    api_keys = {
      "OPENAI_API_KEY": "test-openai-key",
      "ANTHROPIC_API_KEY": "test-anthropic-key",
      "GOOGLE_API_KEY": "test-google-key",
      "OLLAMA_API_KEY": "test-ollama-key",
    }

    with patch("llm_clients.OpenAI") as mock_openai, patch("llm_clients.Anthropic") as mock_anthropic, patch("llm_clients.genai"):
      clients = initialize_clients(api_keys)

      # Test all enabled LLM families are initialized
      assert "openai" in clients
      assert "anthropic" in clients
      assert "google" in clients
      assert "ollama" in clients
      assert "ollama_local" in clients

      # Verify correct client initialization calls
      assert mock_openai.call_count >= 2  # OpenAI + Ollama clients
      mock_anthropic.assert_called_once_with(api_key="test-anthropic-key")

  def test_initialize_clients_anthropic_error(self):
    """Test Anthropic client initialization error handling."""
    api_keys = {
      "OPENAI_API_KEY": "",
      "ANTHROPIC_API_KEY": "invalid-key",
      "GOOGLE_API_KEY": "",
      "OLLAMA_API_KEY": "llama",
    }

    with patch("llm_clients.OpenAI"), patch("llm_clients.Anthropic") as mock_anthropic, patch("llm_clients.genai"):
      # Make Anthropic raise an exception
      mock_anthropic.side_effect = Exception("Invalid API key")

      clients = initialize_clients(api_keys)

      # Should set client to None on error
      assert clients["anthropic"] is None

  def test_initialize_clients_openai_error(self):
    """Test OpenAI client initialization error handling."""
    api_keys = {
      "OPENAI_API_KEY": "invalid-key",
      "ANTHROPIC_API_KEY": "",
      "GOOGLE_API_KEY": "",
      "OLLAMA_API_KEY": "llama",
    }

    with patch("llm_clients.OpenAI") as mock_openai, patch("llm_clients.Anthropic"), patch("llm_clients.genai"):
      # Make OpenAI raise an exception
      mock_openai.side_effect = Exception("Invalid API key")

      clients = initialize_clients(api_keys)

      # Should set client to None on error
      assert clients["openai"] is None

  def test_initialize_clients_google_error(self):
    """Test Google API configuration error handling."""
    api_keys = {
      "OPENAI_API_KEY": "",
      "ANTHROPIC_API_KEY": "",
      "GOOGLE_API_KEY": "invalid-key",
      "OLLAMA_API_KEY": "llama",
    }

    with patch("llm_clients.OpenAI"), patch("llm_clients.Anthropic"), patch("llm_clients.genai") as mock_genai:
      # Make genai.configure raise an exception
      mock_genai.configure.side_effect = Exception("Invalid API key")

      clients = initialize_clients(api_keys)

      # Should set client to None on error
      assert clients["google"] is None


class TestOpenAIProvider:
  """Test OpenAI family LLMs (GPT-4, ChatGPT, O-series)."""

  @patch("llm_clients.OpenAI")
  def test_query_openai_responses_api(self, mock_openai_class):
    """Test OpenAI Responses API."""
    # Setup mock client
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    # Setup mock response with proper Responses API format
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
      "output": [{"type": "message", "content": [{"type": "output_text", "text": "Test response from GPT-4"}]}]
    }
    mock_client.responses.create.return_value = mock_response

    # Test with Responses API
    result = query_openai(
      client=mock_client, query="Test query", system="You are helpful", model="gpt-4o", temperature=0.7, max_tokens=1000, conversation_messages=[]
    )

    assert result == "Test response from GPT-4"
    mock_client.responses.create.assert_called_once()

    # Verify correct parameters were passed
    call_args = mock_client.responses.create.call_args
    assert call_args[1]["model"] == "gpt-4o"
    assert call_args[1]["max_output_tokens"] == 1000
    assert "input" in call_args[1]

  def test_format_messages_for_responses_api(self):
    """Test message formatting for Responses API."""
    messages = [
      {"role": "system", "content": "You are helpful"},
      {"role": "user", "content": "Hello"},
      {"role": "assistant", "content": "Hi there!"},
      {"role": "user", "content": "How are you?"},
    ]

    formatted = format_messages_for_responses_api(messages)

    # Check system -> developer mapping
    assert formatted[0]["role"] == "developer"
    assert formatted[0]["content"][0]["type"] == "input_text"
    assert formatted[0]["content"][0]["text"] == "You are helpful"

    # Check user messages
    assert formatted[1]["role"] == "user"
    assert formatted[1]["content"][0]["type"] == "input_text"

    # Check assistant messages use output_text
    assert formatted[2]["role"] == "assistant"
    assert formatted[2]["content"][0]["type"] == "output_text"

  def test_extract_content_from_response(self):
    """Test content extraction from Responses API response."""
    # Test proper Responses API format
    response_data = {"output": [{"type": "message", "content": [{"type": "output_text", "text": "Extracted text"}]}]}

    content = _extract_content_from_response(response_data)
    assert content == "Extracted text"

    # Test empty response
    assert _extract_content_from_response({}) == ""
    assert _extract_content_from_response(None) == ""

  def test_model_capability_detection(self):
    """Test model capability detection functions."""
    # Test reasoning model detection
    assert _is_reasoning_model("gpt-5") is True
    assert _is_reasoning_model("o1") is True
    assert _is_reasoning_model("o3-mini") is True
    assert _is_reasoning_model("o4-mini") is True
    assert _is_reasoning_model("gpt-5-chat-latest") is False
    assert _is_reasoning_model("gpt-4o") is False

    # Test web search support
    assert _supports_web_search("gpt-5") is True
    assert _supports_web_search("o1") is True
    assert _supports_web_search("gpt-5-chat-latest") is False

    # Test vision support
    assert _supports_vision("gpt-5") is True
    assert _supports_vision("gpt-4o") is True
    assert _supports_vision("o4") is True
    assert _supports_vision("gpt-4.1-nano") is False

    # Test image generation support
    assert _supports_image_generation("gpt-5") is True
    assert _supports_image_generation("o3") is True
    assert _supports_image_generation("gpt-5-nano") is False

  @patch("llm_clients.OpenAI")
  def test_query_openai_reasoning_model_config(self, mock_openai_class):
    """Test OpenAI reasoning model configuration (O4 series)."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    # Setup mock response
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
      "output": [{"type": "message", "content": [{"type": "output_text", "text": "O4 reasoning response"}]}]
    }
    mock_client.responses.create.return_value = mock_response

    # Test with O4 model (should use medium effort)
    result = query_openai(
      client=mock_client,
      query="Complex reasoning task",
      system="You are helpful",
      model="o4-pro",
      temperature=0.7,
      max_tokens=1000,
      conversation_messages=[],
    )

    assert result == "O4 reasoning response"

    # Verify reasoning configuration
    call_args = mock_client.responses.create.call_args
    payload = call_args[1]
    assert "reasoning" in payload
    assert payload["reasoning"]["effort"] == "medium"
    assert payload["text"]["verbosity"] == "medium"

  @patch("llm_clients.OpenAI")
  def test_query_openai_response_fallbacks(self, mock_openai_class):
    """Test OpenAI response content extraction fallbacks."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    # Setup mock response without standard output format
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {}
    mock_response.output = "Fallback output"
    mock_client.responses.create.return_value = mock_response

    result = query_openai(
      client=mock_client,
      query="Test query",
      system="Test system",
      model="gpt-4o",
      temperature=0.7,
      max_tokens=1000,
    )

    # Should fall back to response.output
    assert result == "Fallback output"

  @patch("llm_clients.OpenAI")
  def test_query_openai_auth_error_path(self, mock_openai_class):
    """Test OpenAI authentication error path."""
    from errors import AuthenticationError

    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    # Simulate authentication error with status code
    error = Exception("Invalid API key")
    error.status_code = 401
    mock_client.responses.create.side_effect = error

    with pytest.raises(AuthenticationError, match="Invalid OpenAI API key"):
      query_openai(client=mock_client, query="Test", system="Test", model="gpt-4o", temperature=0.7, max_tokens=100)

  @patch("llm_clients.OpenAI")
  def test_query_openai_rate_limit_path(self, mock_openai_class):
    """Test OpenAI rate limit error path."""
    from errors import APIError

    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    # Simulate rate limit error
    error = Exception("Rate limit exceeded")
    error.status_code = 429
    mock_client.responses.create.side_effect = error

    with pytest.raises(APIError, match="Rate limit exceeded"):
      query_openai(client=mock_client, query="Test", system="Test", model="gpt-4o", temperature=0.7, max_tokens=100)


class TestAnthropicProvider:
  """Test Anthropic family LLMs (Claude models)."""

  @patch("llm_clients.Anthropic")
  def test_query_anthropic_success(self, mock_anthropic_class):
    """Test successful Anthropic Claude query."""
    # Setup mock client
    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client

    # Setup mock response
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = "Claude response"
    mock_client.messages.create.return_value = mock_response

    result = query_anthropic(
      client=mock_client,
      query_text="Test query",
      systemprompt="You are helpful Claude",
      model="claude-3-5-sonnet-latest",
      temperature=0.7,
      max_tokens=1000,
      conversation_messages=[],
    )

    assert result == "Claude response"
    mock_client.messages.create.assert_called_once()

    # Verify correct parameters
    call_args = mock_client.messages.create.call_args
    assert call_args[1]["model"] == "claude-3-5-sonnet-latest"
    assert call_args[1]["temperature"] == 0.7
    assert call_args[1]["max_tokens"] == 1000
    assert call_args[1]["system"] == "You are helpful Claude"

  @patch("llm_clients.Anthropic")
  def test_query_anthropic_claude_37_features(self, mock_anthropic_class):
    """Test Claude 3.7 with 2025 features."""
    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = "Claude 3.7 response with thinking"
    mock_client.messages.create.return_value = mock_response

    result = query_anthropic(
      client=mock_client,
      query_text="Complex reasoning task",
      systemprompt="You are helpful",
      model="claude-3-7-sonnet-20250219",
      temperature=0.7,
      max_tokens=1000,
    )

    assert result == "Claude 3.7 response with thinking"

    # Verify 2025 features in extra_headers
    call_args = mock_client.messages.create.call_args
    extra_headers = call_args[1]["extra_headers"]
    assert "interleaved-thinking-2025-05-14" in extra_headers["anthropic-beta"]
    assert "token-efficient-tools-2025-02-19" in extra_headers["anthropic-beta"]

  @patch("llm_clients.Anthropic")
  def test_query_anthropic_extended_thinking(self, mock_anthropic_class):
    """Test Anthropic models with extended thinking beta header."""
    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client

    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = "Response with extended thinking"
    mock_client.messages.create.return_value = mock_response

    # Test with 3-7 model (should get interleaved-thinking header)
    result = query_anthropic(
      client=mock_client,
      query_text="Test query",
      systemprompt="You are helpful",
      model="claude-3-7-opus-20250515",
      temperature=0.7,
      max_tokens=1000,
    )

    assert result == "Response with extended thinking"
    call_args = mock_client.messages.create.call_args
    extra_headers = call_args[1]["extra_headers"]
    assert "interleaved-thinking-2025-05-14" in extra_headers["anthropic-beta"]


class TestGoogleGeminiProvider:
  """Test Google/Gemini family LLMs."""

  @patch("multiprocessing.get_context")
  def test_query_gemini_success(self, mock_get_context):
    """Test successful Google Gemini query."""
    # Setup mock multiprocessing
    mock_ctx = MagicMock()
    mock_pool = MagicMock()
    mock_pool.apply.return_value = "Gemini response"
    mock_ctx.Pool.return_value.__enter__ = MagicMock(return_value=mock_pool)
    mock_ctx.Pool.return_value.__exit__ = MagicMock(return_value=None)
    mock_get_context.return_value = mock_ctx

    result = query_gemini(
      query="Test query",
      system="You are helpful Gemini",
      model="gemini-2.0-flash",
      temperature=0.7,
      max_tokens=1000,
      api_key="test-google-key",
      conversation_messages=[],
    )

    assert result == "Gemini response"
    mock_pool.apply.assert_called_once()

  @patch("multiprocessing.get_context")
  def test_query_gemini_2025_features(self, mock_get_context):
    """Test Gemini with 2025 optimizations."""
    mock_ctx = MagicMock()
    mock_pool = MagicMock()
    mock_pool.apply.return_value = "Gemini 2.5 response"
    mock_ctx.Pool.return_value.__enter__ = MagicMock(return_value=mock_pool)
    mock_ctx.Pool.return_value.__exit__ = MagicMock(return_value=None)
    mock_get_context.return_value = mock_ctx

    result = query_gemini(
      query="Test query",
      system="You are helpful",
      model="gemini-2.5-pro-exp-03-25",
      temperature=0.8,  # Should use top_p=0.95 optimization
      max_tokens=2000,
      api_key="test-google-key",
    )

    assert result == "Gemini 2.5 response"

  @patch("multiprocessing.get_context")
  def test_query_gemini_subprocess_error(self, mock_get_context):
    """Test Gemini query subprocess error handling."""
    from errors import APIError

    mock_ctx = MagicMock()
    mock_pool = MagicMock()
    # Simulate subprocess returning error
    mock_pool.apply.return_value = "ERROR: API key invalid"
    mock_ctx.Pool.return_value.__enter__ = MagicMock(return_value=mock_pool)
    mock_ctx.Pool.return_value.__exit__ = MagicMock(return_value=None)
    mock_get_context.return_value = mock_ctx

    with pytest.raises(Exception, match="API key invalid"):
      query_gemini(
        query="Test query",
        system="Test",
        model="gemini-2.0-flash",
        temperature=0.7,
        max_tokens=1000,
        api_key="invalid-key",
      )

  @patch("multiprocessing.get_context")
  def test_run_gemini_query_exception(self, mock_get_context):
    """Test Gemini query exception handling for invalid responses."""
    from errors import APIError

    mock_ctx = MagicMock()
    mock_pool = MagicMock()
    # Simulate subprocess returning None (no result)
    mock_pool.apply.return_value = None
    mock_ctx.Pool.return_value.__enter__ = MagicMock(return_value=mock_pool)
    mock_ctx.Pool.return_value.__exit__ = MagicMock(return_value=None)
    mock_get_context.return_value = mock_ctx

    with pytest.raises(Exception, match="did not return a result"):
      query_gemini(
        query="Test query",
        system="Test",
        model="gemini-2.0-flash",
        temperature=0.7,
        max_tokens=1000,
        api_key="test-key",
      )

  @patch("llm_clients.genai")
  def test_get_available_gemini_models_success(self, mock_genai):
    """Test successful retrieval of available Gemini models."""
    from llm_clients import get_available_gemini_models

    # Mock model objects
    mock_model1 = MagicMock()
    mock_model1.name = "models/gemini-2.0-flash"

    mock_model2 = MagicMock()
    mock_model2.name = "models/gemini-2.5-pro"

    mock_embedding = MagicMock()
    mock_embedding.name = "models/embedding-001"

    mock_deprecated = MagicMock()
    mock_deprecated.name = "models/gemini-1.5-pro-001"

    mock_genai.list_models.return_value = [mock_model1, mock_model2, mock_embedding, mock_deprecated]

    result = get_available_gemini_models("test-api-key")

    # Should include non-embedding, non-deprecated models
    assert "models/gemini-2.0-flash" in result
    assert "models/gemini-2.5-pro" in result
    # Should exclude embedding and deprecated models
    assert "models/embedding-001" not in result
    assert "models/gemini-1.5-pro-001" not in result

  @patch("llm_clients.genai")
  def test_get_available_gemini_models_failure(self, mock_genai):
    """Test Gemini model list retrieval failure."""
    from llm_clients import get_available_gemini_models

    # Simulate API error
    mock_genai.list_models.side_effect = Exception("API error")

    result = get_available_gemini_models("test-api-key")

    # Should return empty list on error
    assert result == []


class TestOllamaProvider:
  """Test Ollama family LLMs (Llama, Gemma, etc.)."""

  @patch("llm_clients.requests")
  def test_query_llama_local_success(self, mock_requests):
    """Test successful local Ollama/Llama query."""
    # Setup mock client
    mock_client = MagicMock()
    mock_client.base_url = "http://localhost:11434/v1"

    # Setup mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"message": {"content": "Llama response"}, "done": true}'
    mock_requests.post.return_value = mock_response

    result = query_llama(
      client=mock_client,
      query_text="Test query",
      systemprompt="You are helpful Llama",
      model="gemma3:4b",
      temperature=0.7,
      max_tokens=1000,
      conversation_messages=[],
      api_keys={"OLLAMA_API_KEY": "ollama"},
    )

    assert result == "Llama response"
    mock_requests.post.assert_called_once()

    # Verify request parameters
    call_args = mock_requests.post.call_args
    assert "http://localhost:11434/api/chat" in call_args[0][0]
    request_data = call_args[1]["json"]
    assert request_data["model"] == "gemma3:4b"
    assert request_data["temperature"] == 0.7
    assert request_data["max_tokens"] == 1000

  @patch("llm_clients.requests")
  def test_query_llama_remote_success(self, mock_requests):
    """Test successful remote Ollama query."""
    # Setup mock client for remote
    mock_client = MagicMock()
    mock_client.base_url = "https://ai.okusi.id/api/v1"

    # Setup mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"message": {"content": "Remote Llama response"}, "done": true}'
    mock_requests.post.return_value = mock_response

    result = query_llama(
      client=mock_client,
      query_text="Test query",
      systemprompt="You are helpful",
      model="gemma3:12b",
      temperature=0.8,
      max_tokens=1500,
      api_keys={"OLLAMA_API_KEY": "remote-key"},
    )

    assert result == "Remote Llama response"
    mock_requests.post.assert_called_once()

    # Verify remote URL and auth
    call_args = mock_requests.post.call_args
    assert "ai.okusi.id" in call_args[0][0]
    headers = call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer remote-key"

  @patch("llm_clients.requests")
  def test_query_llama_request_error(self, mock_requests):
    """Test Llama request connection error handling."""
    import requests as real_requests

    mock_client = MagicMock()
    mock_client.base_url = "http://localhost:11434/v1"

    # Simulate connection error using the real RequestException class
    mock_requests.post.side_effect = real_requests.RequestException("Connection refused")
    mock_requests.RequestException = real_requests.RequestException

    with pytest.raises(ValueError, match="Connection error"):
      query_llama(
        client=mock_client,
        query_text="Test query",
        systemprompt="Test",
        model="gemma3:4b",
        temperature=0.7,
        max_tokens=1000,
        api_keys={"OLLAMA_API_KEY": "ollama"},
      )

  @patch("llm_clients.requests")
  def test_query_llama_error_response(self, mock_requests):
    """Test Llama API error response handling."""
    import requests as real_requests

    mock_client = MagicMock()
    mock_client.base_url = "http://localhost:11434/v1"

    # Simulate API error response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": "Model not found"}
    mock_response.text = '{"error": "Model not found"}'
    mock_requests.post.return_value = mock_response
    # Need to provide the real RequestException class for the except clause
    mock_requests.RequestException = real_requests.RequestException

    with pytest.raises(ValueError, match="Ollama API error"):
      query_llama(
        client=mock_client,
        query_text="Test query",
        systemprompt="Test",
        model="nonexistent:model",
        temperature=0.7,
        max_tokens=1000,
        api_keys={"OLLAMA_API_KEY": "ollama"},
      )

  def test_parse_streaming_response_multiline(self):
    """Test parsing multiline streaming response from Ollama."""
    from llm_clients import _parse_streaming_response

    # Simulate streaming response with multiple chunks
    streaming_text = (
      '{"message": {"content": "First chunk "}, "done": false}\n'
      '{"message": {"content": "second chunk "}, "done": false}\n'
      '{"message": {"content": "third chunk"}, "done": true, "total_duration": 1000000, "model": "test"}\n'
    )

    result = _parse_streaming_response(streaming_text)

    # Should concatenate all chunks
    assert result == "First chunk second chunk third chunk"


class TestLLMRouting:
  """Test main query routing to all LLM families."""

  def test_query_routing_openai_family(self):
    """Test query routing for OpenAI family models."""
    clients = {"openai": MagicMock()}
    api_keys = {"OPENAI_API_KEY": "test-key"}
    model_parameters = {"family": "openai", "max_output_tokens": 4000}

    with patch("llm_clients.query_openai") as mock_query_openai:
      mock_query_openai.return_value = "OpenAI response"

      result = query(
        clients=clients,
        query_text="Test query",
        systemprompt="You are helpful",
        messages=[],
        model="gpt-4o",
        temperature=0.7,
        max_tokens=1000,
        model_parameters=model_parameters,
        api_keys=api_keys,
      )

      assert result == "OpenAI response"
      mock_query_openai.assert_called_once()
      # Verify query_openai is called with correct args (no use_responses_api param)
      call_args = mock_query_openai.call_args
      assert "use_responses_api" not in call_args[1]

  def test_query_routing_anthropic_family(self):
    """Test query routing for Anthropic family models."""
    clients = {"anthropic": MagicMock()}
    api_keys = {"ANTHROPIC_API_KEY": "test-key"}
    model_parameters = {"family": "anthropic", "max_output_tokens": 4000}

    with patch("llm_clients.query_anthropic") as mock_query_anthropic:
      mock_query_anthropic.return_value = "Anthropic response"

      result = query(
        clients=clients,
        query_text="Test query",
        systemprompt="You are helpful",
        messages=[],
        model="claude-3-5-sonnet-latest",
        temperature=0.7,
        max_tokens=1000,
        model_parameters=model_parameters,
        api_keys=api_keys,
      )

      assert result == "Anthropic response"
      mock_query_anthropic.assert_called_once()

  def test_query_routing_google_family(self):
    """Test query routing for Google/Gemini family models."""
    clients = {"google": True}
    api_keys = {"GOOGLE_API_KEY": "test-key"}
    model_parameters = {"family": "google", "max_output_tokens": 4000}

    with patch("llm_clients.query_gemini") as mock_query_gemini:
      mock_query_gemini.return_value = "Gemini response"

      result = query(
        clients=clients,
        query_text="Test query",
        systemprompt="You are helpful",
        messages=[],
        model="gemini-2.0-flash",
        temperature=0.7,
        max_tokens=1000,
        model_parameters=model_parameters,
        api_keys=api_keys,
      )

      assert result == "Gemini response"
      mock_query_gemini.assert_called_once()

  def test_query_routing_ollama_family(self):
    """Test query routing for Ollama family models."""
    clients = {"ollama": MagicMock(), "ollama_local": MagicMock()}
    api_keys = {"OLLAMA_API_KEY": "test-key"}
    model_parameters = {"family": "ollama", "max_output_tokens": 4000, "url": "http://localhost:11434"}

    with patch("llm_clients.query_llama") as mock_query_llama:
      mock_query_llama.return_value = "Llama response"

      result = query(
        clients=clients,
        query_text="Test query",
        systemprompt="You are helpful",
        messages=[],
        model="gemma3:4b",
        temperature=0.7,
        max_tokens=1000,
        model_parameters=model_parameters,
        api_keys=api_keys,
      )

      assert result == "Llama response"
      mock_query_llama.assert_called_once()


class TestErrorHandling:
  """Test error handling for all LLM providers."""

  def test_openai_authentication_error(self):
    """Test OpenAI authentication error handling."""
    with patch("llm_clients.OpenAI") as mock_openai_class:
      mock_client = MagicMock()
      mock_openai_class.return_value = mock_client

      # Simulate authentication error on Responses API
      from errors import AuthenticationError

      mock_client.responses.create.side_effect = Exception("invalid_api_key")

      with pytest.raises(AuthenticationError):
        query_openai(client=mock_client, query="Test", system="Test", model="gpt-4o", temperature=0.7, max_tokens=100)

  def test_anthropic_rate_limit_error(self):
    """Test Anthropic rate limit error handling."""
    with patch("llm_clients.Anthropic") as mock_anthropic_class:
      mock_client = MagicMock()
      mock_anthropic_class.return_value = mock_client

      # Simulate rate limit error
      error = Exception("rate limit")
      error.status_code = 429
      mock_client.messages.create.side_effect = error

      from errors import APIError

      with pytest.raises(APIError):
        query_anthropic(client=mock_client, query_text="Test", systemprompt="Test", model="claude-3-5-sonnet-latest", temperature=0.7, max_tokens=100)

  def test_unsupported_model_family(self):
    """Test handling of unsupported model families."""
    clients = {}
    api_keys = {}
    model_parameters = {"family": "unsupported", "max_output_tokens": 4000}

    from errors import ConfigurationError

    with pytest.raises(ConfigurationError):
      query(
        clients=clients,
        query_text="Test query",
        systemprompt="Test",
        messages=[],
        model="unknown-model",
        temperature=0.7,
        max_tokens=1000,
        model_parameters=model_parameters,
        api_keys=api_keys,
      )


if __name__ == "__main__":
  pytest.main([__file__])
