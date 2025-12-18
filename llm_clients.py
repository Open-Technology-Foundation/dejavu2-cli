#!/usr/bin/env python3
"""
LLM client handlers for dejavu2-cli.

This module provides client initialization and query functions for multiple LLM providers:
- OpenAI (GPT-4, GPT-5, O-series reasoning models)
- Anthropic (Claude 3.5, Claude 4 with extended thinking)
- Google (Gemini 2.0/2.5 via google-genai SDK)
- Ollama (local and remote deployments)

Key Features:
- Unified query interface via route_query_by_family()
- Provider-specific exception handling with SDK exception types
- Subprocess isolation for Gemini to suppress GRPC warnings
- Support for reasoning models with configurable effort levels
- Conversation history management for multi-turn interactions

Exception Handling:
- SDK-specific exceptions (anthropic.AuthenticationError, openai.RateLimitError, etc.)
  are caught and converted to custom exceptions from errors.py
- This provides consistent error handling across providers while preserving
  detailed error information for debugging

Google SDK Note:
- Uses google-genai SDK (not google-generativeai) as of 2025
- Client pattern: genai.Client(api_key=...) instead of genai.configure()
- Model listing: client.models.list() instead of genai.list_models()
"""

import json
import logging
import os
from typing import Any

import requests

# Import custom exceptions
from errors import APIError, AuthenticationError, ConfigurationError

# Set environment variables to suppress warnings from Google libraries
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"
os.environ["GRPC_PYTHON_LOG_LEVEL"] = "ERROR"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Import LLM provider libraries
# Note: These are imported at module level for easier mocking in tests
import anthropic
import openai
from google import genai
from anthropic import Anthropic
from openai import OpenAI

# Configure ABSL logging to suppress additional warnings
try:
  import absl.logging

  absl.logging.set_verbosity(absl.logging.ERROR)
  logging.getLogger("absl").propagate = False
except ImportError:
  pass

# Setup module logger
logger = logging.getLogger(__name__)


# API key handling
def get_api_keys() -> dict[str, str]:
  """
  Get API keys from environment variables.

  Returns:
      Dictionary mapping key names to values
  """
  logger.debug("Retrieving API keys from environment variables")

  api_keys = {
    "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
    "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", ""),
    "OLLAMA_API_KEY": os.environ.get("OLLAMA_API_KEY", "llama"),  # Default to 'llama' if not set
  }

  # Log which keys are available (without revealing actual keys)
  available_keys = [name for name, key in api_keys.items() if key]
  missing_keys = [name for name, key in api_keys.items() if not key and name != "OLLAMA_API_KEY"]

  if available_keys:
    logger.info(f"API keys available: {', '.join(available_keys)}")
  if missing_keys:
    logger.warning(f"API keys missing: {', '.join(missing_keys)}")

  return api_keys


# Initialize clients
def initialize_clients(api_keys: dict[str, str]) -> dict[str, Any]:
  """
  Initialize client objects for various LLM providers.

  Creates client instances for Anthropic, OpenAI, Google (Gemini), and Ollama.
  Each client is initialized with error handling for invalid parameters,
  authentication failures, and connection errors. Failed initializations
  result in None values (graceful degradation).

  Args:
      api_keys: Dictionary containing API keys:
          - ANTHROPIC_API_KEY: For Claude models
          - OPENAI_API_KEY: For GPT/O-series models
          - GOOGLE_API_KEY: For Gemini models
          - OLLAMA_API_KEY: For Ollama (defaults to "llama")

  Returns:
      Dictionary with keys: anthropic, openai, google, ollama_local, ollama
      Values are client objects or None if initialization failed.
  """
  clients = {}

  # Anthropic client
  if api_keys["ANTHROPIC_API_KEY"]:
    try:
      clients["anthropic"] = Anthropic(api_key=api_keys["ANTHROPIC_API_KEY"])
      # Use a single consistent beta header with 2025 features (removed deprecated output-128k)
      clients["anthropic"].beta_headers = {"anthropic-beta": "token-efficient-tools-2025-02-19"}
    except (TypeError, ValueError) as e:
      logger.error(f"Anthropic client initialization error (invalid params): {e}")
      clients["anthropic"] = None
    except anthropic.AuthenticationError as e:
      logger.error(f"Anthropic authentication error: {e}")
      clients["anthropic"] = None
    except anthropic.APIConnectionError as e:
      logger.error(f"Anthropic connection error: {e}")
      clients["anthropic"] = None
  else:
    clients["anthropic"] = None

  # OpenAI client
  if api_keys["OPENAI_API_KEY"]:
    try:
      clients["openai"] = OpenAI(api_key=api_keys["OPENAI_API_KEY"])
    except (TypeError, ValueError) as e:
      logger.error(f"OpenAI client initialization error (invalid params): {e}")
      clients["openai"] = None
    except openai.AuthenticationError as e:
      logger.error(f"OpenAI authentication error: {e}")
      clients["openai"] = None
    except openai.APIConnectionError as e:
      logger.error(f"OpenAI connection error: {e}")
      clients["openai"] = None
  else:
    clients["openai"] = None

  # Google client - using new google-genai SDK
  if api_keys["GOOGLE_API_KEY"]:
    try:
      clients["google"] = genai.Client(api_key=api_keys["GOOGLE_API_KEY"])
    except (ValueError, TypeError, AttributeError) as e:
      logger.error(f"Google client initialization error: {e}")
      clients["google"] = None
  else:
    clients["google"] = None

  # Initialize both local and remote Ollama clients
  try:
    # Local Ollama client
    clients["ollama_local"] = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
  except (TypeError, ValueError) as e:
    logger.warning(f"Local Ollama client initialization error (invalid params): {e}")
    clients["ollama_local"] = None
  except ConnectionError as e:
    logger.warning(f"Local Ollama client connection error: {e}")
    clients["ollama_local"] = None

  # Remote Ollama client initialization
  try:
    if api_keys.get("OLLAMA_API_KEY") and os.environ.get("OLLAMA_REMOTE_URL"):
      # Only use remote URL if explicitly configured via environment variable
      remote_url = os.environ.get("OLLAMA_REMOTE_URL")
      # Warn user about remote endpoint usage
      logging.warning(f"Using remote Ollama endpoint: {remote_url}")
      # Ensure we have the /v1/chat/completions endpoint
      if not remote_url.endswith("/v1"):
        remote_url = f"{remote_url}/v1"

      clients["ollama"] = OpenAI(
        base_url=remote_url,
        api_key=api_keys.get("OLLAMA_API_KEY"),  # Require explicit API key
      )
    else:
      clients["ollama"] = clients["ollama_local"]  # Fallback to local
  except (TypeError, ValueError) as e:
    logger.warning(f"Remote Ollama client initialization error (invalid params): {e}")
    clients["ollama"] = clients["ollama_local"]  # Fallback to local
  except ConnectionError as e:
    logger.warning(f"Remote Ollama client connection error: {e}")
    clients["ollama"] = clients["ollama_local"]  # Fallback to local

  return clients


# Query functions
def query_anthropic(
  client: Anthropic,
  query_text: str,
  systemprompt: str,
  model: str,
  temperature: float,
  max_tokens: int,
  conversation_messages: list[dict[str, str]] | None = None,
) -> str:
  """
  Send a query to the Anthropic API and return the response.

  Supports Claude 3.5, 3.7, and 4.x models with appropriate beta headers
  for features like extended thinking and token-efficient tools.

  Args:
      client: Anthropic client object
      query_text: The user's query or prompt
      systemprompt: System prompt that guides the model's behavior
      model: The Anthropic Claude model name to use
      temperature: Sampling temperature (higher = more random)
      max_tokens: Maximum number of tokens in the response
      conversation_messages: Optional list of previous messages for multi-turn

  Returns:
      The model's response as a string

  Raises:
      ValueError: If the Anthropic client is None (missing API key)
      AuthenticationError: Invalid API key
      APIError: Rate limit, bad request, connection, or other API errors
  """
  try:
    # Check if we have a valid client
    if client is None:
      raise ValueError("Set ANTHROPIC_API_KEY environment variable")

    # Prepare extra headers - removed deprecated output-128k-2025-02-19
    extra_headers = {}

    # Add special beta headers for specific models and 2025 features
    if "sonnet" in model and "3-7" in model:
      # Claude 3.7 Sonnet with latest 2025 features (removed deprecated output-128k)
      extra_headers["anthropic-beta"] = "interleaved-thinking-2025-05-14,token-efficient-tools-2025-02-19"
    elif "sonnet" in model:
      # For other sonnet models with 2025 improvements
      extra_headers["anthropic-beta"] = "max-tokens-3-5-sonnet-2024-07-15,token-efficient-tools-2025-02-19"
    elif "3-7" in model:
      # For Claude 3.7 models with latest features (removed deprecated output-128k)
      extra_headers["anthropic-beta"] = "interleaved-thinking-2025-05-14"

    # Prepare messages with conversation history if provided
    messages = []

    # Add conversation history if available
    if conversation_messages:
      messages.extend(conversation_messages)

    # Add the current query as the last message
    messages.append({"role": "user", "content": query_text})

    # Make the API call with conversation history included
    message = client.messages.create(
      max_tokens=max_tokens,
      messages=messages,
      model=model,
      system=systemprompt,
      temperature=temperature,
      extra_headers=extra_headers,
    )

    return message.content[0].text
  except ValueError:
    # Re-raise ValueError (missing client) as-is
    raise
  except anthropic.AuthenticationError as e:
    logger.error(f"{model} authentication failed: {e}")
    raise AuthenticationError(f"Invalid Anthropic API key for {model}: {e}") from e
  except anthropic.RateLimitError as e:
    logger.error(f"{model} rate limit exceeded: {e}")
    raise APIError(f"Rate limit exceeded for {model}: {e}") from e
  except anthropic.BadRequestError as e:
    logger.error(f"{model} bad request: {e}")
    raise APIError(f"Bad request for {model}: {e}") from e
  except anthropic.APIConnectionError as e:
    logger.error(f"{model} connection error: {e}")
    raise APIError(f"Connection error for {model}: {e}") from e
  except anthropic.InternalServerError as e:
    logger.error(f"{model} server error: {e}")
    raise APIError(f"Anthropic server error for {model}: {e}") from e
  except anthropic.APIStatusError as e:
    logger.error(f"{model} API status error: {e}")
    raise APIError(f"Anthropic API error for {model}: {e}") from e
  except (IndexError, AttributeError) as e:
    logger.error(f"{model} response extraction error: {e}")
    raise APIError(f"Invalid response format from {model}: {e}") from e


# OpenAI model capability detection functions
def _is_reasoning_model(model: str) -> bool:
  """
  Check if a model supports reasoning parameter.

  Args:
      model: Model name (may include date suffix)

  Returns:
      True if model supports reasoning
  """
  model_lower = model.lower()

  # gpt-5-chat-latest doesn't support reasoning
  if "gpt-5-chat" in model_lower:
    return False

  # Check if model starts with reasoning-capable prefixes
  reasoning_prefixes = ("gpt-5", "o1", "o3", "o4")
  return any(model_lower.startswith(prefix) for prefix in reasoning_prefixes)


def _supports_web_search(model: str) -> bool:
  """
  Check if a model supports web search.

  Args:
      model: Model name (may include date suffix)

  Returns:
      True if model supports web search
  """
  model_lower = model.lower()

  # gpt-5-chat does NOT support web search
  if "gpt-5-chat" in model_lower:
    return False

  # Models that support web search
  web_search_prefixes = ("gpt-5", "o1", "o3", "o4")
  return any(model_lower.startswith(prefix) for prefix in web_search_prefixes)


def _supports_vision(model: str) -> bool:
  """
  Check if a model supports vision input (images).

  Args:
      model: Model name (may include date suffix)

  Returns:
      True if model supports vision
  """
  model_lower = model.lower()

  # Models that support vision
  vision_prefixes = ("gpt-5", "gpt-4.1", "gpt-4o", "o4")

  # Check for specific models that don't support vision
  no_vision_models = ("gpt-4.1-nano", "codex")
  if any(no_vis in model_lower for no_vis in no_vision_models):
    return False

  return any(model_lower.startswith(prefix) for prefix in vision_prefixes)


def _supports_image_generation(model: str) -> bool:
  """
  Check if a model supports image generation tool.

  Args:
      model: Model name (may include date suffix)

  Returns:
      True if model supports image generation
  """
  model_lower = model.lower()

  # Models that support image generation
  image_gen_prefixes = ("gpt-5", "gpt-4.1", "gpt-4o", "o3", "o4")

  # Exclude certain models
  if "nano" in model_lower or "codex" in model_lower:
    return False

  return any(model_lower.startswith(prefix) for prefix in image_gen_prefixes)


def format_messages_for_responses_api(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
  """
  Format messages for the Responses API input format.

  Args:
      messages: List of message objects with 'role' and 'content'

  Returns:
      Formatted input array for Responses API
  """
  formatted_messages = []

  for message in messages:
    role = message["role"]
    content = message["content"]

    # Map roles (system becomes developer in Responses API)
    if role == "system":
      role = "developer"
    elif role not in ["user", "assistant", "developer"]:
      role = "user"

    # Determine content type based on role
    # Assistant messages use output_text, others use input_text
    text_type = "output_text" if role == "assistant" else "input_text"

    # Handle different content types
    if isinstance(content, list):
      # Already structured content
      content_items = []
      for block in content:
        if block.get("type") == "text":
          content_items.append({"type": text_type, "text": block["text"]})
        # Handle images if present (not implemented in current dv2)
      formatted_messages.append({"role": role, "content": content_items})
    else:
      # Simple text content
      formatted_messages.append({"role": role, "content": [{"type": text_type, "text": content}]})

  return formatted_messages


def _extract_content_from_response(data: dict[str, Any]) -> str:
  """
  Extract message content from Responses API response.

  Args:
      data: Response data from API

  Returns:
      Extracted text content or empty string
  """
  if not data:
    return ""

  # Try Responses API format
  if "output" in data and isinstance(data["output"], list):
    for output_item in data["output"]:
      if output_item.get("type") == "message":
        content_list = output_item.get("content", [])
        if isinstance(content_list, list):
          for content_item in content_list:
            if isinstance(content_item, dict):
              if content_item.get("type") == "output_text":
                return content_item.get("text", "")
              elif "text" in content_item:
                return content_item["text"]

  return ""


def query_openai(
  client: OpenAI, query: str, system: str, model: str, temperature: float, max_tokens: int, conversation_messages: list[dict[str, str]] | None = None
) -> str:
  """
  Send a query to the OpenAI API using the Responses API.

  Supports GPT-4/5 and O-series reasoning models. Reasoning models (O1, O3, O4)
  use configurable effort levels:
  - O4 and chat models: "medium" effort (required by API)
  - Other reasoning models: "minimal" effort (faster responses)

  Args:
      client: OpenAI client object
      query: The user's query or prompt
      system: System prompt that guides the model's behavior
      model: The OpenAI model name to use
      temperature: Sampling temperature (ignored for reasoning models)
      max_tokens: Maximum number of tokens in the response
      conversation_messages: Optional list of previous messages for multi-turn

  Returns:
      The model's response as a string

  Raises:
      ValueError: If the OpenAI client is None
      AuthenticationError: Invalid API key
      APIError: Rate limit, bad request, connection, or server errors
  """
  try:
    # Check if we have a valid client
    if client is None:
      raise ValueError("OpenAI client initialization failed. Check API key validity.")

    # Prepare messages list
    messages = [{"role": "system", "content": system}]

    # Add conversation history if available
    if conversation_messages:
      messages.extend(conversation_messages)

    # Add current query
    messages.append({"role": "user", "content": query})

    # Format messages for Responses API
    formatted_input = format_messages_for_responses_api(messages)

    # Build payload for Responses API
    payload = {"model": model, "input": formatted_input}

    # Check model capabilities
    model_lower = model.lower()
    is_reasoning_model = _is_reasoning_model(model)

    # Configure based on model type
    if is_reasoning_model:
      # Reasoning models configuration
      # O4 models and chat models (gpt-5.2-chat) require "medium" effort
      # Other reasoning models can use "minimal" for faster responses
      if model_lower.startswith("o4") or "chat" in model_lower:
        payload["reasoning"] = {"effort": "medium"}
        payload["text"] = {"verbosity": "medium"}
      else:
        payload["reasoning"] = {"effort": "minimal"}
        payload["text"] = {"verbosity": "low"}
    else:
      # Non-reasoning models
      payload["text"] = {"verbosity": "medium"}
      # Temperature supported for non-reasoning models without tools
      if not model_lower.startswith("codex"):
        payload["temperature"] = temperature

    # Add max tokens
    if max_tokens:
      payload["max_output_tokens"] = max_tokens

    # Make the API call using the Responses endpoint
    response = client.responses.create(**payload)

    # Extract content from response
    content = _extract_content_from_response(response.model_dump() if hasattr(response, "model_dump") else dict(response))

    if not content:
      # Try to extract error or fallback to string representation
      if hasattr(response, "output"):
        content = response.output
      elif hasattr(response, "content"):
        content = response.content
      elif hasattr(response, "text"):
        content = response.text
      else:
        content = str(response)

    return content

  except ValueError:
    # Re-raise ValueError (missing client) as-is
    raise
  except openai.AuthenticationError as e:
    logger.error(f"{model} authentication failed: {e}")
    raise AuthenticationError(f"Invalid OpenAI API key for {model}: {e}") from e
  except openai.RateLimitError as e:
    logger.error(f"{model} rate limit exceeded: {e}")
    raise APIError(f"Rate limit exceeded for {model}: {e}") from e
  except openai.BadRequestError as e:
    logger.error(f"{model} bad request: {e}")
    raise APIError(f"Bad request for {model}: {e}") from e
  except openai.APIConnectionError as e:
    logger.error(f"{model} connection error: {e}")
    raise APIError(f"Connection error for {model}: {e}") from e
  except openai.APIStatusError as e:
    logger.error(f"{model} API status error (status {e.status_code}): {e}")
    if e.status_code >= 500:
      raise APIError(f"OpenAI server error for {model}: {e}") from e
    raise APIError(f"OpenAI API error for {model}: {e}") from e
  except (AttributeError, KeyError, IndexError) as e:
    logger.error(f"{model} response extraction error: {e}")
    raise APIError(f"Invalid response format from {model}: {e}") from e


def prepare_llama_messages(query_text: str, systemprompt: str, conversation_messages: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
  """
  Prepare message list for LLaMA query.

  Args:
    query_text: The user's query or prompt
    systemprompt: System prompt that guides the model's behavior
    conversation_messages: Optional list of previous messages from conversation history

  Returns:
    List of messages formatted for API
  """
  # Build message list starting with system prompt
  messages = [{"role": "system", "content": systemprompt}]

  # Add conversation history if available
  if conversation_messages:
    # Add conversation history, skipping system messages (we already added our own)
    for msg in conversation_messages:
      if msg["role"] != "system":
        messages.append(msg)

  # Add the current query as the final message
  messages.append({"role": "user", "content": query_text})

  return messages


def prepare_llama_request(
  client: OpenAI, model: str, messages: list[dict[str, str]], temperature: float, max_tokens: int, api_keys: dict[str, str] | None = None
) -> tuple:
  """
  Prepare request parameters for LLaMA query.

  Args:
    client: OpenAI client configured for Ollama
    model: The LLaMA model name to use
    messages: List of messages to send
    temperature: Sampling temperature
    max_tokens: Maximum number of tokens in the response
    api_keys: Dictionary containing API keys

  Returns:
    Tuple of (request_url, headers, request_params)
  """
  # Convert URL object to string for safer comparison
  base_url_str = str(client.base_url) if client.base_url else ""
  is_remote = "okusi.id" in base_url_str or "https://" in base_url_str

  # Prepare request parameters - keeping it simple for Ollama
  request_params = {"model": model, "messages": messages, "stream": False, "max_tokens": max_tokens}

  # Only include temperature if it's not zero (Ollama default)
  if temperature > 0:
    request_params["temperature"] = temperature

  # Get the API key
  api_key = "ollama"  # Default for local
  if is_remote and api_keys:
    api_key = api_keys.get("OLLAMA_API_KEY", "llama")

  # Determine the correct URL for chat endpoint
  if is_remote:
    # Remote URL format - use configured endpoint
    request_url = base_url_str.replace("/v1", "")
    if not request_url.endswith("/chat"):
      request_url = f"{request_url}/chat"
  else:
    # Local URL format - 'http://localhost:11434/api/chat'
    request_url = "http://localhost:11434/api/chat"

  # Prepare headers
  headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

  return request_url, headers, request_params


def execute_llama_request(request_url: str, headers: dict[str, str], request_params: dict[str, Any]) -> requests.Response:
  """
  Execute HTTP request to LLaMA API.

  Args:
    request_url: URL to send request to
    headers: HTTP headers
    request_params: Request parameters

  Returns:
    Response object

  Raises:
    ValueError: If request fails
  """
  logger.debug(f"Sending request to Ollama API: {request_url}")

  try:
    # Make the HTTP request to the Ollama chat API
    response = requests.post(request_url, headers=headers, json=request_params, timeout=60)

    # Check for error response
    if response.status_code != 200:
      # Try to extract error message from JSON response
      try:
        error_data = response.json()
        if "error" in error_data:
          logger.error(f"Ollama API error: {error_data['error']}")
          raise ValueError(f"Ollama API error: {error_data['error']}")
      except json.JSONDecodeError:
        pass

      # Generic error if we couldn't parse the error message
      logger.error(f"Request failed with status {response.status_code}: {response.text}")
      raise ValueError(f"API error: {response.status_code} - {response.text}")

    return response

  except requests.RequestException as e:
    logger.error(f"HTTP request failed: {e}")
    raise ValueError(f"Connection error: {e}") from e


def process_llama_response(response: requests.Response, model: str) -> str:
  """
  Process and extract content from Ollama API response.

  Handles both streaming and non-streaming response formats from Ollama,
  extracting the assistant's message content and logging relevant metadata.

  Args:
    response: HTTP response object from Ollama API request
    model: Model name for logging and error context

  Returns:
    str: The assistant's response text extracted from the API response

  Raises:
    ValueError: If response format is invalid or content cannot be extracted

  Note:
    Automatically detects response format (streaming vs. standard) and
    processes accordingly. Logs token usage and timing metadata when available.
  """
  response_text = response.text

  # Handle line-delimited JSON responses (streaming format)
  if "\n" in response_text and response_text.strip().startswith("{"):
    return _parse_streaming_response(response_text)

  # Handle single JSON object response (non-streaming format)
  try:
    data = json.loads(response_text)

    # Check for the standard Ollama chat endpoint format
    if "message" in data and "content" in data["message"]:
      # Extract metadata for logging if available
      if data.get("done", False):
        _log_response_metadata(data, model)

      # Check for model unloading
      if data.get("done_reason") == "unload":
        logger.warning(f"Model {model} was unloaded during processing")

      return data["message"]["content"]

    # For generate endpoint fallback (API variation)
    elif "response" in data:
      # Log warning about unexpected format
      logger.warning("Received 'response' format instead of 'message.content' format")
      return data["response"]
  except json.JSONDecodeError as e:
    logger.error(f"Failed to parse JSON response: {e}")

    # If it doesn't look like JSON, return the raw text as a last resort
    if not (response_text.strip().startswith("{") or response_text.strip().startswith("[")):
      return response_text

    raise ValueError(f"Failed to parse response from Ollama API: {e}") from e

  # If we got here, we couldn't extract the content
  raise ValueError("Failed to extract content from Ollama API response")


def query_llama(
  client: OpenAI,
  query_text: str,
  systemprompt: str,
  model: str,
  temperature: float,
  max_tokens: int,
  conversation_messages: list[dict[str, str]] | None = None,
  api_keys: dict[str, str] | None = None,
) -> str:
  """
  Send a query to a local or remote LLaMA-based model via an Ollama server.

  Uses the Ollama /api/chat endpoint to generate responses. Handles both streaming
  and non-streaming responses in the format documented in the Ollama API.

  Args:
      client: OpenAI client configured for Ollama
      query_text: The user's query or prompt
      systemprompt: System prompt that guides the model's behavior
      model: The LLaMA model name to use
      temperature: Sampling temperature (higher = more random)
      max_tokens: Maximum number of tokens in the response
      conversation_messages: Optional list of previous messages from conversation history
      api_keys: Dictionary containing API keys

  Returns:
      The model's response as a string

  Raises:
      Exception: If the Ollama server is not running or returns an error
  """
  try:
    # Prepare messages
    messages = prepare_llama_messages(query_text, systemprompt, conversation_messages)

    # Prepare request parameters
    request_url, headers, request_params = prepare_llama_request(client, model, messages, temperature, max_tokens, api_keys)

    # Execute request
    response = execute_llama_request(request_url, headers, request_params)

    # Process response
    return process_llama_response(response, model)

  except ValueError as e:
    logger.error(f"{model} query failed (invalid parameters): {e}")
    raise APIError(f"Ollama query error for {model}: {e}") from e
  except requests.RequestException as e:
    logger.error(f"{model} query failed (connection error): {e}")
    raise APIError(f"Ollama connection error for {model}: {e}") from e
  except json.JSONDecodeError as e:
    logger.error(f"{model} query failed (invalid JSON response): {e}")
    raise APIError(f"Ollama response parsing error for {model}: {e}") from e


def _parse_streaming_response(response_text: str) -> str:
  """Parse a streaming response from the Ollama API."""
  full_content = ""
  final_metadata = None

  # Process each line as a separate JSON object
  for line in response_text.splitlines():
    if not line or not line.strip():
      continue

    try:
      # Parse the line as JSON
      json_obj = json.loads(line)

      # Check if this is the standard chat endpoint format
      if "message" in json_obj and "content" in json_obj["message"]:
        full_content += json_obj["message"]["content"]

        # Store metadata from the final response
        if json_obj.get("done", False):
          final_metadata = json_obj

      # If this is the last chunk, log metadata
      if json_obj.get("done", False) and final_metadata:
        _log_response_metadata(final_metadata, json_obj.get("model", "unknown"))

    except json.JSONDecodeError:
      # Skip invalid JSON lines
      continue

  return full_content


def _log_response_metadata(data: dict[str, Any], model: str) -> None:
  """Log useful metadata from the Ollama API response."""
  metadata_fields = ["total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration", "eval_count", "eval_duration"]

  metadata = {field: data.get(field) for field in metadata_fields if field in data}

  if metadata:
    # Convert nanoseconds to milliseconds for readability
    for field in ["total_duration", "load_duration", "prompt_eval_duration", "eval_duration"]:
      if field in metadata and metadata[field]:
        metadata[field] = f"{metadata[field] / 1000000:.2f}ms"

    logger.debug(f"Model {model} response metadata: {metadata}")


def _run_gemini_query_in_process(query_data):
  """
  Execute Gemini query in a separate process to isolate GRPC warnings.

  This function runs in an isolated subprocess and handles the Gemini API
  interactions using the new google-genai SDK. Redirects stderr to suppress
  all GRPC-related warnings.

  Args:
      query_data: Tuple containing (query, system, model, temperature,
                 max_tokens, api_key, conversation_messages)

  Returns:
      The response text or error message prefixed with "ERROR:"
  """
  import os
  import sys

  # Redirect stderr to /dev/null to suppress warnings
  stderr_fd = sys.stderr.fileno()
  with open(os.devnull, "w") as devnull:
    os.dup2(devnull.fileno(), stderr_fd)

  # Unpack arguments
  query, system, model, temperature, max_tokens, api_key, conversation_messages = query_data

  # Import the new google-genai SDK in this process
  from google import genai
  from google.genai import types

  try:
    # Create client with API key
    client = genai.Client(api_key=api_key)

    # Set up generation config with 2025 improvements
    gen_config = types.GenerateContentConfig(
      temperature=temperature,
      max_output_tokens=max_tokens,
      # Use updated top_p for better performance (2025 optimization)
      top_p=0.95 if temperature > 0 else None,
    )

    # Build contents for the query
    if conversation_messages and len(conversation_messages) > 0:
      # Build message history for conversation mode
      contents = []

      # Add system prompt as first user message
      contents.append(types.Content(
        role="user",
        parts=[types.Part(text=f"<s>\n{system}\n</s>")]
      ))

      # Add model acknowledgment
      contents.append(types.Content(
        role="model",
        parts=[types.Part(text="Understood. I will follow these instructions.")]
      ))

      # Add conversation history
      for msg in conversation_messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(
          role=role,
          parts=[types.Part(text=msg["content"])]
        ))

      # Add current query
      contents.append(types.Content(
        role="user",
        parts=[types.Part(text=query)]
      ))

      # Generate response with history
      response = client.models.generate_content(
        model=model,
        contents=contents,
        config=gen_config,
      )
    else:
      # Simple query without conversation
      prompt = f"<s>\n{system}\n</s>\n\n{query}"
      response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=gen_config,
      )

    # Extract response text with multiple fallback options
    result = ""
    try:
      # Try standard accessors first
      if hasattr(response, "text"):
        result = response.text
      elif hasattr(response, "candidates") and response.candidates:
        if hasattr(response.candidates[0], "content"):
          content = response.candidates[0].content
          if hasattr(content, "parts") and content.parts:
            result = content.parts[0].text
          else:
            result = str(content)
        elif hasattr(response.candidates[0], "parts"):
          result = response.candidates[0].parts[0].text
        else:
          result = str(response.candidates[0])
      else:
        result = str(response)
    except (AttributeError, IndexError, TypeError):
      # Last resort: convert to string
      result = str(response.candidates[0]) if hasattr(response, "candidates") and response.candidates else str(response)

    return result
  except Exception as e:
    return f"ERROR: {str(e)}"


def query_gemini(
  query: str, system: str, model: str, temperature: float, max_tokens: int, api_key: str, conversation_messages: list[dict[str, str]] | None = None
) -> str:
  """
  Send a query to the Google Gemini API and return the response.

  Uses a subprocess to isolate GRPC warnings and prevent them from being
  displayed after successful query completion. Handles both conversation-based
  and single-query modes.

  Args:
      query: The user's query or prompt
      system: System prompt that guides the model's behavior
      model: The Gemini model name to use
      temperature: Sampling temperature (higher = more random)
      max_tokens: Maximum number of tokens in the response
      api_key: Google API key
      conversation_messages: Optional conversation history

  Returns:
      The model's response as a string

  Raises:
      ValueError: For invalid parameters
      Exception: If the API request fails
  """
  # Check if Google API key is set
  if not api_key:
    raise ValueError("Missing Google API key. Set GOOGLE_API_KEY environment variable.")

  try:
    # Import multiprocessing here to avoid any circular imports
    import multiprocessing

    # Package all parameters for the subprocess
    query_data = (query, system, model, temperature, max_tokens, api_key, conversation_messages)

    # Create an isolated process for Gemini API operations
    # Using 'spawn' context prevents inheriting file descriptors that could leak GRPC resources
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(processes=1) as pool:
      # Run the query in the isolated process
      result = pool.apply(_run_gemini_query_in_process, (query_data,))
      pool.close()
      pool.terminate()

    # Handle potential error responses
    if result and isinstance(result, str) and result.startswith("ERROR:"):
      raise Exception(result[6:])  # Strip "ERROR:" prefix

    # Return valid result
    if result:
      return result

    # If we got here without a result, raise an exception
    raise Exception(f"Model {model} did not return a result")

  except ValueError as ve:
    # Specific handling for API key issues
    if "api_key" in str(ve).lower():
      raise AuthenticationError(f"Invalid Google API key: {ve}") from ve
    raise
  except Exception as e:
    # Log and re-raise with additional context
    logger.error(f"{model} query failed: {e}")
    error_str = str(e).lower()
    if "authentication" in error_str or "api_key" in error_str:
      raise AuthenticationError(f"Authentication failed for {model}: Invalid/expired Google API key") from e
    elif "quota" in error_str or "rate limit" in error_str:
      raise APIError(f"Rate limit or quota exceeded for {model}") from e

    # Re-raise as APIError with context
    raise APIError(f"Google API error for {model}: {e}") from e


def get_available_gemini_models(api_key: str) -> list[str]:
  """
  Retrieve a list of available text-based Gemini models from the Google API.

  Uses the new google-genai SDK to list available models. Filters out models
  that are not suitable for text generation, including embedding models and
  other excluded model types.

  Args:
      api_key: Google API key

  Returns:
      List of model names available through the Google Generative AI API

  Raises:
      Exception: If the API request fails
  """
  if not api_key:
    return []

  try:
    # Use new google-genai SDK
    client = genai.Client(api_key=api_key)
    available_models = client.models.list()
    excluded_models = [
      "models/aqa",
      "models/chat-bison-001",
      "models/text-bison-001",
      "models/gemini-1.0-pro-latest",
      "models/gemini-1.0-pro-vision-latest",
      "models/gemini-pro-vision",
      "models/gemini-1.5-pro-002",
      # Exclude deprecated models as of 2025
      "models/gemini-1.5-pro-001",
      "models/gemini-1.5-flash-001",
    ]
    text_models = [model.name for model in available_models if "embedding" not in model.name and model.name not in excluded_models]
    return text_models
  except Exception as e:
    logger.error(f"Cannot list Gemini models: {e}")
    return []


def validate_query_parameters(model: str, max_tokens: int, model_parameters: dict[str, Any]) -> int:
  """
  Validate and adjust query parameters.

  Args:
    model: The model name
    max_tokens: Maximum number of tokens requested
    model_parameters: Model-specific parameters

  Returns:
    Adjusted max_tokens value
  """
  logger.info(f"Processing query using model: {model}")

  # Ensure max_tokens doesn't exceed model limit
  model_max_tokens = model_parameters.get("max_output_tokens", 4000)
  if max_tokens > model_max_tokens:
    logger.warning(f"Requested max_tokens ({max_tokens}) exceeds model limit, using model maximum ({model_max_tokens})")
    max_tokens = model_max_tokens

  return max_tokens


def prepare_query_context(query_text: str, systemprompt: str, messages: list[dict[str, str]]) -> tuple:
  """
  Prepare query context and process system prompt.

  Args:
    query_text: The user's query
    systemprompt: System prompt
    messages: Conversation messages

  Returns:
    Tuple of (query_text, processed_systemprompt, conversation_messages)
  """
  # Check if conversation history is included
  conversation_messages = None
  if messages:
    conversation_messages = messages

  # Process time/date placeholders in system prompt
  from utils import spacetime_placeholders

  processed_systemprompt = spacetime_placeholders(systemprompt)

  return query_text, processed_systemprompt, conversation_messages


def get_anthropic_client(clients: dict[str, Any]) -> Any:
  """
  Get and validate Anthropic client.

  Args:
    clients: Dictionary of clients

  Returns:
    Anthropic client

  Raises:
    ValueError: If client not available
  """
  client = clients.get("anthropic")
  if client is None:
    logger.error("Anthropic client not available, API key might be missing")
    raise ValueError("Anthropic client not available. Please check API key.")
  return client


def get_openai_client(clients: dict[str, Any]) -> Any:
  """
  Get and validate OpenAI client.

  Args:
    clients: Dictionary of clients

  Returns:
    OpenAI client

  Raises:
    ValueError: If client not available
  """
  client = clients.get("openai")
  if client is None:
    logger.error("OpenAI client not available, API key might be missing")
    raise ValueError("OpenAI client not available. Please check API key.")
  return client


def get_ollama_client(clients: dict[str, Any], model_parameters: dict[str, Any]) -> Any:
  """
  Get appropriate Ollama client (local or remote).

  Args:
    clients: Dictionary of clients
    model_parameters: Model parameters

  Returns:
    Ollama client

  Raises:
    ValueError: If client not available
  """
  # Determine if we should use local or remote client based on URL
  model_url = model_parameters.get("url", "")
  client = None

  # Convert URL to string for safer comparison
  model_url_str = str(model_url) if model_url else ""

  # Check for specific remote URL patterns
  if any(pattern in model_url_str for pattern in ["okusi.id", "https://", "http://", "api"]):
    # Use remote client
    client = clients.get("ollama")
    if client is None:
      client = clients.get("ollama_local")
  else:
    # Use local client
    client = clients.get("ollama_local", clients.get("ollama"))

  if client is None:
    logger.error("Ollama client not available, local server might not be running")
    raise ValueError("Ollama client not available. Is the Ollama server running?")

  return client


def validate_google_api_key(api_keys: dict[str, str]) -> str:
  """
  Validate Google API key availability.

  Args:
    api_keys: Dictionary of API keys

  Returns:
    Google API key

  Raises:
    AuthenticationError: If API key not available
  """
  if not api_keys.get("GOOGLE_API_KEY"):
    logger.error("Google API key not available")
    raise AuthenticationError("Google API key not available. Please check environment variables.")
  return api_keys["GOOGLE_API_KEY"]


def route_query_by_family(
  model_family: str,
  model: str,
  clients: dict[str, Any],
  query_text: str,
  systemprompt: str,
  temperature: float,
  max_tokens: int,
  conversation_messages: list[dict[str, str]],
  model_parameters: dict[str, Any],
  api_keys: dict[str, str],
) -> str:
  """
  Route query based on model family.

  Args:
    model_family: The model family
    model: The model name
    clients: Dictionary of clients
    query_text: User query
    systemprompt: System prompt
    temperature: Sampling temperature
    max_tokens: Maximum tokens
    conversation_messages: Conversation history
    model_parameters: Model parameters
    api_keys: API keys

  Returns:
    Model response

  Raises:
    Various exceptions based on provider
  """
  if not model:
    raise ValueError("Model name cannot be None or empty")

  match model_family:
    case "anthropic":
      client = get_anthropic_client(clients)
      return query_anthropic(client, query_text, systemprompt, model, temperature, max_tokens, conversation_messages)

    case "google":
      google_api_key = validate_google_api_key(api_keys)
      return query_gemini(query_text, systemprompt, model, temperature, max_tokens, google_api_key, conversation_messages)

    case "ollama":
      client = get_ollama_client(clients, model_parameters)
      return query_llama(client, query_text, systemprompt, model, temperature, max_tokens, conversation_messages, api_keys=api_keys)

    case "openai" | _ if model and model.startswith(("gpt", "chatgpt", "o1", "o3", "o4")):
      client = get_openai_client(clients)

      # Special handling for O-series models
      if model and model.startswith(("o1", "o3", "o4")):
        temperature = 1

      return query_openai(client, query_text, systemprompt, model, temperature, max_tokens, conversation_messages)

    case _:
      return None


def route_query_by_name(
  model: str,
  clients: dict[str, Any],
  query_text: str,
  systemprompt: str,
  temperature: float,
  max_tokens: int,
  conversation_messages: list[dict[str, str]],
  api_keys: dict[str, str],
) -> str | None:
  """
  Route query based on model name prefixes as fallback.

  Args:
    model: The model name
    clients: Dictionary of clients
    query_text: User query
    systemprompt: System prompt
    temperature: Sampling temperature
    max_tokens: Maximum tokens
    conversation_messages: Conversation history
    api_keys: API keys

  Returns:
    Model response or None if no match
  """
  if model and model.startswith("claude"):
    client = get_anthropic_client(clients)
    return query_anthropic(client, query_text, systemprompt, model, temperature, max_tokens, conversation_messages)

  elif model and model.startswith(("llama", "nemo", "gemma")):
    client = clients.get("ollama")
    if client is None:
      logger.error("Ollama client not available, server might not be running")
      raise APIError("Ollama client not available. Is the Ollama server running?")

    return query_llama(client, query_text, systemprompt, model, temperature, max_tokens, conversation_messages, api_keys=api_keys)

  elif model and model.startswith("gemini"):
    google_api_key = validate_google_api_key(api_keys)
    return query_gemini(query_text, systemprompt, model, temperature, max_tokens, google_api_key, conversation_messages)

  return None


def query(
  clients: dict[str, Any],
  query_text: str,
  systemprompt: str,
  messages: list[dict[str, str]],
  model: str,
  temperature: float,
  max_tokens: int,
  model_parameters: dict[str, Any],
  api_keys: dict[str, str],
) -> str:
  """
  Route the query to the appropriate API based on the model specified.

  Args:
      clients: Dictionary of initialized API clients
      query_text: The user's query or prompt
      systemprompt: System prompt that guides the model's behavior
      messages: List of previous messages in the conversation (if any)
      model: The canonical model name to use
      temperature: Sampling temperature (higher = more random)
      max_tokens: Maximum number of tokens in the response
      model_parameters: Dictionary containing model-specific parameters
      api_keys: Dictionary containing API keys

  Returns:
      The model's response as a string

  Raises:
      ValueError: If an unknown model is specified
  """
  try:
    # Validate and adjust parameters
    max_tokens = validate_query_parameters(model, max_tokens, model_parameters)

    # Prepare query context
    query_text, systemprompt, conversation_messages = prepare_query_context(query_text, systemprompt, messages)

    # Determine provider based on family first
    model_family = model_parameters.get("family", "").lower()

    # Try routing by family first
    result = route_query_by_family(
      model_family, model, clients, query_text, systemprompt, temperature, max_tokens, conversation_messages, model_parameters, api_keys
    )

    if result is not None:
      return result

    # Fallback to model name prefixes if family not recognized
    result = route_query_by_name(model, clients, query_text, systemprompt, temperature, max_tokens, conversation_messages, api_keys)

    if result is not None:
      return result

    # No matching provider found
    logger.error(f"Unknown model family '{model_family}' for model '{model}', cannot route query")
    raise ConfigurationError(f"Unknown model family '{model_family}' for model '{model}'. Check Models.json for available models.")

  except Exception as e:
    logger.error(f"Error querying model {model}: {str(e)}", exc_info=True)
    raise


# fin
