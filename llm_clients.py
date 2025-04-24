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
            # Use a single consistent beta header
            clients['anthropic'].beta_headers = {
                "anthropic-beta": "output-128k-2025-02-19"
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
            
        # Prepare extra headers - ensure they match beta_headers set on the client
        extra_headers = {
            "anthropic-beta": "output-128k-2025-02-19"
        }
        
        # Add special beta headers for specific models
        if 'sonnet' in model:
            # For any sonnet model
            extra_headers["anthropic-beta"] = "max-tokens-3-5-sonnet-2024-07-15"
        elif '3-7' in model:
            # For Claude 3.7 models
            extra_headers["anthropic-beta"] = "output-128k-2025-02-19"
        
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
        if "invalid_api_key" in str(e).lower() or "authentication" in str(e).lower():
            raise ValueError(f"{model}: Invalid/expired API key")
        raise

def query_openai(
    client: OpenAI,
    query: str,
    system: str,
    model: str,
    temperature: float,
    max_tokens: int,
    conversation_messages: List[Dict[str, str]] = None
) -> str:
    """
    Send a query to the OpenAI API and return the response.
    
    Args:
        client: OpenAI client object
        query: The user's query or prompt
        system: System prompt that guides the model's behavior
        model: The OpenAI model name to use
        temperature: Sampling temperature (higher = more random)
        max_tokens: Maximum number of tokens in the response
        conversation_messages: Optional list of previous messages from conversation history
        
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
    except Exception as e:
        logger.error(f"Error querying {model}: {e}")
        if "invalid_api_key" in str(e).lower() or "authentication" in str(e).lower():
            raise ValueError(f"Authentication error for {model}: Invalid or expired OpenAI API key")
        raise

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
            
            # Process the response
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
            
        except requests.RequestException as e:
            logger.error(f"HTTP request failed: {e}")
            raise ValueError(f"Connection error: {e}")
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
        
        # Set up generation parameters
        gen_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
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
            raise ValueError(f"Invalid Google API key: {ve}")
        raise ve
    except Exception as e:
        # Log and re-raise with additional context
        logger.error(f"{model} query failed: {e}")
        if "authentication" in str(e).lower():
            raise ValueError(f"{model}: Invalid/expired API key")
        raise

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
            "models/gemini-1.5-pro-002"
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
    logger.info(f"Processing query using model: {model}")
    
    # Check if conversation history is included
    conversation_messages = None
    if messages:
        conversation_messages = messages
    
    # Ensure max_tokens doesn't exceed model limit
    model_max_tokens = model_parameters.get('max_output_tokens', 4000)
    if max_tokens > model_max_tokens:
        logger.warning(
            f"Requested max_tokens ({max_tokens}) exceeds model limit, "
            f"using model maximum ({model_max_tokens})"
        )
        max_tokens = model_max_tokens

    # Process time/date placeholders in system prompt
    from utils import spacetime_placeholders
    original_systemprompt = systemprompt
    systemprompt = spacetime_placeholders(systemprompt)

    # Determine provider based on family, then model name as fallback
    model_family = model_parameters.get('family', '').lower()
    
    try:
        # Route based on model family first (matches llm_query.php behavior)
        if model_family == 'anthropic':
            client = clients.get('anthropic')
            if client is None:
                logger.error("Anthropic client not available, API key might be missing")
                raise ValueError("Anthropic client not available. Please check API key.")
                
            return query_anthropic(
                client, query_text, systemprompt, model, 
                temperature, max_tokens, conversation_messages
            )
            
        elif model_family == 'google':
            if not api_keys.get('GOOGLE_API_KEY'):
                logger.error("Google API key not available")
                raise ValueError("Google API key not available. Please check environment variables.")
                
            return query_gemini(
                query_text, systemprompt, model, temperature, max_tokens, 
                api_keys['GOOGLE_API_KEY'], conversation_messages
            )
            
        elif model_family == 'ollama':
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
                
            return query_llama(
                client, query_text, systemprompt, model, 
                temperature, max_tokens, conversation_messages,
                api_keys=api_keys
            )
            
        elif model_family == 'openai' or model.startswith(('gpt', 'chatgpt', 'o1', 'o3', 'o4')):
            client = clients.get('openai')
            if client is None:
                logger.error("OpenAI client not available, API key might be missing")
                raise ValueError("OpenAI client not available. Please check API key.")

            if model.startswith(('o1', 'o3', 'o4')):
                temperature = 1
                    
            return query_openai(
                client, query_text, systemprompt, model, 
                temperature, max_tokens, conversation_messages
            )
            
        # Fallback to model name prefixes if family not recognized
        elif model.startswith('claude'):
            client = clients.get('anthropic')
            if client is None:
                logger.error("Anthropic client not available, API key might be missing")
                raise ValueError("Anthropic client not available. Please check API key.")
                
            return query_anthropic(
                client, query_text, systemprompt, model, 
                temperature, max_tokens, conversation_messages
            )
            
        elif model.startswith(('llama', 'nemo', 'gemma')):
            client = clients.get('ollama')
            if client is None:
                logger.error("Ollama client not available, server might not be running")
                raise ValueError("Ollama client not available. Is the Ollama server running?")
                
            return query_llama(
                client, query_text, systemprompt, model, 
                temperature, max_tokens, conversation_messages,
                api_keys=api_keys
            )
            
        elif model.startswith('gemini'):
            if not api_keys.get('GOOGLE_API_KEY'):
                logger.error("Google API key not available")
                raise ValueError("Google API key not available. Please check environment variables.")
                
            return query_gemini(
                query_text, systemprompt, model, temperature, max_tokens, 
                api_keys['GOOGLE_API_KEY'], conversation_messages
            )
            
        else:
            logger.error(f"Unknown model family '{model_family}' for model '{model}', cannot route query")
            raise ValueError(f"Unknown model family '{model_family}' for model '{model}'. Check Models.json for available models.")
            
    except Exception as e:
        logger.error(f"Error querying model {model}: {str(e)}", exc_info=True)
        raise
        
#fin