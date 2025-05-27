#!/usr/bin/env python3
"""
LLM client handlers for dejavu2-cli.

This module contains client initialization and query functions for
various LLM providers: OpenAI, Anthropic, Google, and both local and remote Ollama models.
"""
import os
import logging
import click
import json
import re
import requests
from typing import Dict, Any, List, Optional

# Import custom exceptions
from errors import AuthenticationError, APIError, ConfigurationError

# Set environment variables to suppress warnings from Google libraries
import os
os.environ['GRPC_ENABLE_FORK_SUPPORT'] = '0'
os.environ['GRPC_PYTHON_LOG_LEVEL'] = 'ERROR'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Import LLM provider libraries
from anthropic import Anthropic
from openai import OpenAI
import google.generativeai as genai

# Configure ABSL logging to suppress additional warnings
try:
    import absl.logging
    absl.logging.set_verbosity(absl.logging.ERROR)
    logging.getLogger('absl').propagate = False
except ImportError:
    pass

# Setup module logger
logger = logging.getLogger(__name__)

# API key handling
def get_api_keys() -> Dict[str, str]:
    """
    Get API keys from environment variables.
    
    Returns:
        Dictionary mapping key names to values
    """
    logger.debug("Retrieving API keys from environment variables")
    
    api_keys = {
        'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY', ''),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', ''),
        'GOOGLE_API_KEY': os.environ.get('GOOGLE_API_KEY', ''),
        'OLLAMA_API_KEY': os.environ.get('OLLAMA_API_KEY', 'llama')  # Default to 'llama' if not set
    }
    
    # Log which keys are available (without revealing actual keys)
    available_keys = [name for name, key in api_keys.items() if key]
    missing_keys = [name for name, key in api_keys.items() if not key and name != 'OLLAMA_API_KEY']
    
    if available_keys:
        logger.info(f"API keys available: {', '.join(available_keys)}")
    if missing_keys:
        logger.warning(f"API keys missing: {', '.join(missing_keys)}")
        
    return api_keys

# Initialize clients
def initialize_clients(api_keys: Dict[str, str]) -> Dict[str, Any]:
    """
    Initialize client objects for various LLM providers.
    
    Args:
        api_keys: Dictionary containing API keys for each provider
        
    Returns:
        Dictionary mapping provider names to client objects
    """
    clients = {}
    
    # Anthropic client
    if api_keys['ANTHROPIC_API_KEY']:
        try:
            clients['anthropic'] = Anthropic(api_key=api_keys['ANTHROPIC_API_KEY'])
            # Use a single consistent beta header with 2025 features (removed deprecated output-128k)
            clients['anthropic'].beta_headers = {
                "anthropic-beta": "token-efficient-tools-2025-02-19"
            }
        except Exception as e:
            logger.error(f"Anthropic client error: {e}")
            clients['anthropic'] = None
    else:
        clients['anthropic'] = None

    # OpenAI client
    if api_keys['OPENAI_API_KEY']:
        try:
            clients['openai'] = OpenAI(api_key=api_keys['OPENAI_API_KEY'])
        except Exception as e:
            logger.error(f"OpenAI client error: {e}")
            clients['openai'] = None
    else:
        clients['openai'] = None

    # Google client
    if api_keys['GOOGLE_API_KEY']:
        try:
            genai.configure(api_key=api_keys['GOOGLE_API_KEY'])
            clients['google'] = True  # Just a flag that it's configured
        except Exception as e:
            logger.error(f"Google API error: {e}")
            clients['google'] = None
    else:
        clients['google'] = None

    # Initialize both local and remote Ollama clients
    try:
        # Local Ollama client
        clients['ollama_local'] = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
    except Exception as e:
        logger.warning(f"Local Ollama client initialization error: {e}")
        clients['ollama_local'] = None
    
    # Remote Ollama client initialization
    try:
        if api_keys.get('OLLAMA_API_KEY'):
            # The URL format depends on the implementation - we need compatibility with okusi.id API
            remote_url = 'https://ai.okusi.id/api'
            # Ensure we have the /v1/chat/completions endpoint
            if not remote_url.endswith('/v1'):
                remote_url = f"{remote_url}/v1"
                
            clients['ollama'] = OpenAI(
                base_url=remote_url,
                api_key=api_keys.get('OLLAMA_API_KEY', 'llama')
            )
        else:
            clients['ollama'] = clients['ollama_local']  # Fallback to local
    except Exception as e:
        logger.warning(f"Remote Ollama client initialization error: {e}")
        clients['ollama'] = clients['ollama_local']  # Fallback to local
    
    return clients

# Query functions
def query_anthropic(
    client: Anthropic,
    query_text: str,
    systemprompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    conversation_messages: List[Dict[str, str]] = None
) -> str:
    """
    Send a query to the Anthropic API and return the response.
    
    Args:
        client: Anthropic client object
        query_text: The user's query or prompt
        systemprompt: System prompt that guides the model's behavior
        model: The Anthropic Claude model name to use
        temperature: Sampling temperature (higher = more random)
        max_tokens: Maximum number of tokens in the response
        conversation_messages: Optional list of previous messages from conversation history
        
    Returns:
        The model's response as a string
        
    Raises:
        ValueError: If the Anthropic API key is missing
        Exception: If the API request fails
    """
    try:
        # Check if we have a valid client
        if client is None:
            raise ValueError("Set ANTHROPIC_API_KEY environment variable")
            
        # Prepare extra headers - removed deprecated output-128k-2025-02-19
        extra_headers = {}
        
        # Add special beta headers for specific models and 2025 features
        if 'sonnet' in model and '3-7' in model:
            # Claude 3.7 Sonnet with latest 2025 features (removed deprecated output-128k)
            extra_headers["anthropic-beta"] = "interleaved-thinking-2025-05-14,token-efficient-tools-2025-02-19"
        elif 'sonnet' in model:
            # For other sonnet models with 2025 improvements
            extra_headers["anthropic-beta"] = "max-tokens-3-5-sonnet-2024-07-15,token-efficient-tools-2025-02-19"
        elif '3-7' in model:
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
    except Exception as e:
        logger.error(f"{model} query failed: {e}")
        # Check for specific Anthropic exceptions
        if hasattr(e, 'status_code'):
            if e.status_code == 401:
                raise AuthenticationError(f"Invalid Anthropic API key for {model}")
            elif e.status_code == 429:
                raise APIError(f"Rate limit exceeded for {model}")
            elif e.status_code >= 500:
                raise APIError(f"Anthropic server error for {model}: {e}")
        
        # Fallback for string matching (less reliable but necessary for some cases)
        error_str = str(e).lower()
        if "invalid_api_key" in error_str or "authentication" in error_str:
            raise AuthenticationError(f"Authentication failed for {model}: Invalid/expired API key")
        elif "rate limit" in error_str:
            raise APIError(f"Rate limit exceeded for {model}")
        
        # Re-raise as APIError with context
        raise APIError(f"Anthropic API error for {model}: {e}")

def query_openai(
    client: OpenAI,
    query: str,
    system: str,
    model: str,
    temperature: float,
    max_tokens: int,
    conversation_messages: List[Dict[str, str]] = None,
    use_responses_api: bool = True
) -> str:
    """
    Send a query to the OpenAI API using Responses API with Chat Completions fallback.
    
    Args:
        client: OpenAI client object
        query: The user's query or prompt
        system: System prompt that guides the model's behavior
        model: The OpenAI model name to use
        temperature: Sampling temperature (higher = more random)
        max_tokens: Maximum number of tokens in the response
        conversation_messages: Optional list of previous messages from conversation history
        use_responses_api: Whether to use the new Responses API (default: True)
        
    Returns:
        The model's response as a string
        
    Raises:
        ValueError: If the OpenAI API key is missing or invalid
        Exception: If the API request fails
    """
    try:
        # Check if we have a valid client
        if client is None:
            raise ValueError("OpenAI client initialization failed. Check API key validity.")
        
        # Use Responses API by default for future-proofing
        if use_responses_api:
            return _query_openai_responses(
                client, query, system, model, temperature, max_tokens, conversation_messages
            )
        
        # Fallback to Chat Completions API if explicitly requested
        return _query_openai_chat_completions(
            client, query, system, model, temperature, max_tokens, conversation_messages
        )
    except Exception as e:
        logger.error(f"Error querying {model}: {e}")
        # Check for specific OpenAI exceptions
        error_type = type(e).__name__
        if hasattr(e, 'status_code'):
            if e.status_code == 401:
                raise AuthenticationError(f"Invalid OpenAI API key for {model}")
            elif e.status_code == 429:
                raise APIError(f"Rate limit exceeded for {model}")
            elif e.status_code >= 500:
                raise APIError(f"OpenAI server error for {model}: {e}")
        
        # Fallback for string matching
        error_str = str(e).lower()
        if "invalid_api_key" in error_str or "authentication" in error_str:
            raise AuthenticationError(f"Authentication failed for {model}: Invalid/expired OpenAI API key")
        elif "rate limit" in error_str:
            raise APIError(f"Rate limit exceeded for {model}")
        
        # Re-raise as APIError with context
        raise APIError(f"OpenAI API error for {model}: {e}")

def _query_openai_chat_completions(
    client: OpenAI,
    query: str,
    system: str,
    model: str,
    temperature: float,
    max_tokens: int,
    conversation_messages: List[Dict[str, str]] = None
) -> str:
    """
    Internal function to handle Chat Completions API requests.
    """
    # Create base messages list with system prompt
    messages = [{"role": "system", "content": system}]
    
    # Add conversation history if available
    if conversation_messages:
        for msg in conversation_messages:
            # Skip system messages as we already added our system prompt
            if msg["role"] != "system":
                messages.append(msg)
    
    # Add current query as the final message
    messages.append({"role": "user", "content": query})
    
    try:
        # First try with max_completion_tokens for all OpenAI models
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_tokens,
        )
    except Exception as oe:
        # If max_completion_tokens fails, fall back to max_tokens
        if "max_completion_tokens" in str(oe):
            logger.warning(f"Error with max_completion_tokens for {model}, trying with max_tokens: {oe}")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                n=1, stop=''
            )
        # If that fails too, try without parameter constraints
        elif "max_tokens" in str(oe):
            logger.warning(f"Error with max_tokens for {model}, trying without token limit: {oe}")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
        else:
            # Re-raise if it's not a token parameter issue
            raise
    return response.choices[0].message.content

def _query_openai_responses(
    client: OpenAI,
    query: str,
    system: str,
    model: str,
    temperature: float,
    max_tokens: int,
    conversation_messages: List[Dict[str, str]] = None
) -> str:
    """
    Internal function to handle Responses API requests (future-proofing).
    
    The Responses API provides stateful conversation management and built-in tools.
    This implementation handles both new conversations and continuing existing ones.
    """
    try:
        # Check if client has responses attribute (Responses API support)
        if not hasattr(client, 'responses'):
            logger.warning(f"Responses API not available, falling back to Chat Completions for {model}")
            return _query_openai_chat_completions(
                client, query, system, model, temperature, max_tokens, conversation_messages
            )
        
        # Prepare the input for Responses API
        # The Responses API uses a simpler input format
        full_input = f"{system}\n\n{query}"
        
        # Add conversation history to input if available
        if conversation_messages:
            history_text = "\n".join([
                f"{msg['role'].title()}: {msg['content']}"
                for msg in conversation_messages
                if msg['role'] != 'system'
            ])
            full_input = f"{system}\n\nConversation History:\n{history_text}\n\nCurrent Query: {query}"
        
        # Create request using Responses API
        response = client.responses.create(
            model=model,
            input=full_input,
            # Note: Responses API may have different parameter names
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        
        # Extract response content
        if hasattr(response, 'output'):
            return response.output
        elif hasattr(response, 'content'):
            return response.content
        elif hasattr(response, 'text'):
            return response.text
        else:
            # Fallback: convert to string
            return str(response)
            
    except Exception as re:
        # If Responses API fails, log and fallback to Chat Completions
        logger.warning(f"Responses API failed for {model}, falling back to Chat Completions: {re}")
        return _query_openai_chat_completions(
            client, query, system, model, temperature, max_tokens, conversation_messages
        )

def prepare_llama_messages(query_text: str, systemprompt: str, conversation_messages: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
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


def prepare_llama_request(client: OpenAI, model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int, api_keys: Dict[str, str] = None) -> tuple:
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
  is_remote = 'okusi.id' in base_url_str or 'https://' in base_url_str
  
  # Prepare request parameters - keeping it simple for Ollama
  request_params = {
    "model": model,
    "messages": messages,
    "stream": False,
    "max_tokens": max_tokens
  }
  
  # Only include temperature if it's not zero (Ollama default)
  if temperature > 0:
    request_params["temperature"] = temperature
    
  # Get the API key
  api_key = 'ollama'  # Default for local
  if is_remote and api_keys:
    api_key = api_keys.get('OLLAMA_API_KEY', 'llama')
    
  # Determine the correct URL for chat endpoint
  if is_remote:
    # Remote URL format - 'https://ai.okusi.id/api/chat'
    request_url = base_url_str.replace('/v1', '')
    if not request_url.endswith('/chat'):
      request_url = f"{request_url}/chat"
  else:
    # Local URL format - 'http://localhost:11434/api/chat'
    request_url = 'http://localhost:11434/api/chat'
  
  # Prepare headers
  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
  }
  
  return request_url, headers, request_params


def execute_llama_request(request_url: str, headers: Dict[str, str], request_params: Dict[str, Any]) -> requests.Response:
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
    response = requests.post(
      request_url,
      headers=headers,
      json=request_params,
      timeout=60
    )
    
    # Check for error response
    if response.status_code != 200:
      # Try to extract error message from JSON response
      try:
        error_data = response.json()
        if 'error' in error_data:
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
    raise ValueError(f"Connection error: {e}")


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
  if '\n' in response_text and response_text.strip().startswith('{'):
    return _parse_streaming_response(response_text)
  
  # Handle single JSON object response (non-streaming format)
  try:
    data = json.loads(response_text)
    
    # Check for the standard Ollama chat endpoint format
    if 'message' in data and 'content' in data['message']:
      # Extract metadata for logging if available
      if data.get('done', False):
        _log_response_metadata(data, model)
      
      # Check for model unloading
      if data.get('done_reason') == 'unload':
        logger.warning(f"Model {model} was unloaded during processing")
      
      return data['message']['content']
    
    # For generate endpoint fallback (API variation)
    elif 'response' in data:
      # Log warning about unexpected format
      logger.warning(f"Received 'response' format instead of 'message.content' format")
      return data['response']
  except json.JSONDecodeError as e:
    logger.error(f"Failed to parse JSON response: {e}")
    
    # If it doesn't look like JSON, return the raw text as a last resort
    if not (response_text.strip().startswith('{') or response_text.strip().startswith('[')):
      return response_text
      
    raise ValueError(f"Failed to parse response from Ollama API: {e}")
  
  # If we got here, we couldn't extract the content
  raise ValueError("Failed to extract content from Ollama API response")


def query_llama(
    client: OpenAI,
    query_text: str,
    systemprompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    conversation_messages: List[Dict[str, str]] = None,
    api_keys: Dict[str, str] = None
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
        request_url, headers, request_params = prepare_llama_request(
            client, model, messages, temperature, max_tokens, api_keys
        )
        
        # Execute request
        response = execute_llama_request(request_url, headers, request_params)
        
        # Process response
        return process_llama_response(response, model)
        
    except Exception as e:
        # Error has already been logged, just pass it up
        logger.error(f"{model} query failed: {e}")
        raise

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
            if 'message' in json_obj and 'content' in json_obj['message']:
                full_content += json_obj['message']['content']
                
                # Store metadata from the final response
                if json_obj.get('done', False):
                    final_metadata = json_obj
            
            # If this is the last chunk, log metadata
            if json_obj.get('done', False) and final_metadata:
                _log_response_metadata(final_metadata, json_obj.get('model', 'unknown'))
                
        except json.JSONDecodeError:
            # Skip invalid JSON lines
            continue
    
    return full_content

def _log_response_metadata(data: Dict[str, Any], model: str) -> None:
    """Log useful metadata from the Ollama API response."""
    metadata_fields = [
        'total_duration', 'load_duration', 'prompt_eval_count',
        'prompt_eval_duration', 'eval_count', 'eval_duration'
    ]
    
    metadata = {field: data.get(field) for field in metadata_fields if field in data}
    
    if metadata:
        # Convert nanoseconds to milliseconds for readability
        for field in ['total_duration', 'load_duration', 'prompt_eval_duration', 'eval_duration']:
            if field in metadata and metadata[field]:
                metadata[field] = f"{metadata[field] / 1000000:.2f}ms"
                
        logger.debug(f"Model {model} response metadata: {metadata}")

def _run_gemini_query_in_process(query_data):
    """
    Execute Gemini query in a separate process to isolate GRPC warnings.
    
    This function runs in an isolated subprocess and handles the Gemini API 
    interactions. Redirects stderr to suppress all GRPC-related warnings.
    
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
    with open(os.devnull, 'w') as devnull:
        os.dup2(devnull.fileno(), stderr_fd)
    
    # Unpack arguments
    query, system, model, temperature, max_tokens, api_key, conversation_messages = query_data
    
    # Import the genai module in this process
    import google.generativeai as genai
    
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Set up generation parameters with 2025 improvements
        gen_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            # Use updated top_p for better performance (2025 optimization)
            top_p=0.95 if temperature > 0 else None,
        )
        
        # Initialize model and get response based on whether we have conversation history
        if conversation_messages and len(conversation_messages) > 0:
            # Create chat session with history
            model_obj = genai.GenerativeModel(model, generation_config=gen_config)
            chat = model_obj.start_chat(history=[])
            
            # Add system prompt
            system_prompt = f"<s>\n{system}\n</s>"
            chat.send_message(system_prompt)
            
            # Add conversation history
            for msg in conversation_messages:
                if msg["role"] == "user":
                    chat.send_message(msg["content"])
                elif msg["role"] == "assistant":
                    # Add assistant messages to history
                    history = chat.history
                    history.append({"role": "model", "parts": [{"text": msg["content"]}]})
            
            # Send current query
            response = chat.send_message(query)
        else:
            # Simple query without conversation
            prompt = f"<s>\n{system}\n</s>\n\n{query}"
            model_obj = genai.GenerativeModel(model, generation_config=gen_config)
            response = model_obj.generate_content(prompt)
        
        # Extract response text with multiple fallback options
        result = ""
        try:
            # Try standard accessors first
            if hasattr(response, 'text'):
                result = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                if hasattr(response.candidates[0], 'content'):
                    result = response.candidates[0].content
                elif hasattr(response.candidates[0], 'parts'):
                    result = response.candidates[0].parts[0].text
                else:
                    result = str(response.candidates[0])
            else:
                result = str(response)
        except Exception:
            # Last resort: convert to string
            if hasattr(response, 'candidates') and response.candidates:
                result = str(response.candidates[0])
            else:
                result = str(response)
        
        return result
    except Exception as e:
        return f"ERROR: {str(e)}"

def query_gemini(
    query: str,
    system: str,
    model: str,
    temperature: float,
    max_tokens: int,
    api_key: str,
    conversation_messages: List[Dict[str, str]] = None
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
        ctx = multiprocessing.get_context('spawn')
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
            raise AuthenticationError(f"Invalid Google API key: {ve}")
        raise ve
    except Exception as e:
        # Log and re-raise with additional context
        logger.error(f"{model} query failed: {e}")
        error_str = str(e).lower()
        if "authentication" in error_str or "api_key" in error_str:
            raise AuthenticationError(f"Authentication failed for {model}: Invalid/expired Google API key")
        elif "quota" in error_str or "rate limit" in error_str:
            raise APIError(f"Rate limit or quota exceeded for {model}")
        
        # Re-raise as APIError with context
        raise APIError(f"Google API error for {model}: {e}")

def get_available_gemini_models(api_key: str) -> List[str]:
    """
    Retrieve a list of available text-based Gemini models from the Google API.
    
    Filters out models that are not suitable for text generation, including embedding 
    models and other excluded model types.
    
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
        genai.configure(api_key=api_key)
        available_models = genai.list_models()
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
            "models/gemini-1.5-flash-001"
        ]
        text_models = [
            model.name
            for model in available_models
            if "embedding" not in model.name and model.name not in excluded_models
        ]
        return text_models
    except Exception as e:
        logger.error(f"Cannot list Gemini models: {e}")
        return []

def validate_query_parameters(model: str, max_tokens: int, model_parameters: Dict[str, Any]) -> int:
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
  model_max_tokens = model_parameters.get('max_output_tokens', 4000)
  if max_tokens > model_max_tokens:
    logger.warning(
      f"Requested max_tokens ({max_tokens}) exceeds model limit, "
      f"using model maximum ({model_max_tokens})"
    )
    max_tokens = model_max_tokens
  
  return max_tokens


def prepare_query_context(query_text: str, systemprompt: str, messages: List[Dict[str, str]]) -> tuple:
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


def get_anthropic_client(clients: Dict[str, Any]) -> Any:
  """
  Get and validate Anthropic client.
  
  Args:
    clients: Dictionary of clients
    
  Returns:
    Anthropic client
    
  Raises:
    ValueError: If client not available
  """
  client = clients.get('anthropic')
  if client is None:
    logger.error("Anthropic client not available, API key might be missing")
    raise ValueError("Anthropic client not available. Please check API key.")
  return client


def get_openai_client(clients: Dict[str, Any]) -> Any:
  """
  Get and validate OpenAI client.
  
  Args:
    clients: Dictionary of clients
    
  Returns:
    OpenAI client
    
  Raises:
    ValueError: If client not available
  """
  client = clients.get('openai')
  if client is None:
    logger.error("OpenAI client not available, API key might be missing")
    raise ValueError("OpenAI client not available. Please check API key.")
  return client


def get_ollama_client(clients: Dict[str, Any], model_parameters: Dict[str, Any]) -> Any:
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
  model_url = model_parameters.get('url', '')
  client = None
  
  # Convert URL to string for safer comparison
  model_url_str = str(model_url) if model_url else ""
  
  # Check for specific remote URL patterns
  if any(pattern in model_url_str for pattern in ['okusi.id', 'https://', 'http://', 'api']):
    # Use remote client
    client = clients.get('ollama')
    if client is None:
      client = clients.get('ollama_local')
  else:
    # Use local client
    client = clients.get('ollama_local', clients.get('ollama'))
    
  if client is None:
    logger.error("Ollama client not available, local server might not be running")
    raise ValueError("Ollama client not available. Is the Ollama server running?")
    
  return client


def validate_google_api_key(api_keys: Dict[str, str]) -> str:
  """
  Validate Google API key availability.
  
  Args:
    api_keys: Dictionary of API keys
    
  Returns:
    Google API key
    
  Raises:
    AuthenticationError: If API key not available
  """
  if not api_keys.get('GOOGLE_API_KEY'):
    logger.error("Google API key not available")
    raise AuthenticationError("Google API key not available. Please check environment variables.")
  return api_keys['GOOGLE_API_KEY']


def route_query_by_family(model_family: str, model: str, clients: Dict[str, Any], 
                         query_text: str, systemprompt: str, temperature: float, 
                         max_tokens: int, conversation_messages: List[Dict[str, str]], 
                         model_parameters: Dict[str, Any], api_keys: Dict[str, str]) -> str:
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
  if model_family == 'anthropic':
    client = get_anthropic_client(clients)
    return query_anthropic(
      client, query_text, systemprompt, model, 
      temperature, max_tokens, conversation_messages
    )
    
  elif model_family == 'google':
    google_api_key = validate_google_api_key(api_keys)
    return query_gemini(
      query_text, systemprompt, model, temperature, max_tokens, 
      google_api_key, conversation_messages
    )
    
  elif model_family == 'ollama':
    client = get_ollama_client(clients, model_parameters)
    return query_llama(
      client, query_text, systemprompt, model, 
      temperature, max_tokens, conversation_messages,
      api_keys=api_keys
    )
    
  elif model_family == 'openai' or model.startswith(('gpt', 'chatgpt', 'o1', 'o3', 'o4')):
    client = get_openai_client(clients)
    
    # Special handling for O-series models
    if model.startswith(('o1', 'o3', 'o4')):
      temperature = 1
        
    return query_openai(
      client, query_text, systemprompt, model, 
      temperature, max_tokens, conversation_messages,
      use_responses_api=False  # Keep disabled due to format issues
    )
  
  return None


def route_query_by_name(model: str, clients: Dict[str, Any], query_text: str, 
                       systemprompt: str, temperature: float, max_tokens: int, 
                       conversation_messages: List[Dict[str, str]], api_keys: Dict[str, str]) -> Optional[str]:
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
  if model.startswith('claude'):
    client = get_anthropic_client(clients)
    return query_anthropic(
      client, query_text, systemprompt, model, 
      temperature, max_tokens, conversation_messages
    )
    
  elif model.startswith(('llama', 'nemo', 'gemma')):
    client = clients.get('ollama')
    if client is None:
      logger.error("Ollama client not available, server might not be running")
      raise APIError("Ollama client not available. Is the Ollama server running?")
      
    return query_llama(
      client, query_text, systemprompt, model, 
      temperature, max_tokens, conversation_messages,
      api_keys=api_keys
    )
    
  elif model.startswith('gemini'):
    google_api_key = validate_google_api_key(api_keys)
    return query_gemini(
      query_text, systemprompt, model, temperature, max_tokens, 
      google_api_key, conversation_messages
    )
  
  return None


def query(
    clients: Dict[str, Any],
    query_text: str,
    systemprompt: str,
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    model_parameters: Dict[str, Any],
    api_keys: Dict[str, str]
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
        model_family = model_parameters.get('family', '').lower()
        
        # Try routing by family first
        result = route_query_by_family(
            model_family, model, clients, query_text, systemprompt, 
            temperature, max_tokens, conversation_messages, model_parameters, api_keys
        )
        
        if result is not None:
            return result
        
        # Fallback to model name prefixes if family not recognized
        result = route_query_by_name(
            model, clients, query_text, systemprompt, 
            temperature, max_tokens, conversation_messages, api_keys
        )
        
        if result is not None:
            return result
        
        # No matching provider found
        logger.error(f"Unknown model family '{model_family}' for model '{model}', cannot route query")
        raise ConfigurationError(f"Unknown model family '{model_family}' for model '{model}'. Check Models.json for available models.")
            
    except Exception as e:
        logger.error(f"Error querying model {model}: {str(e)}", exc_info=True)
        raise
        
#fin