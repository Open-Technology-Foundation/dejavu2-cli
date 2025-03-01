#!/usr/bin/env python3
"""
LLM client handlers for dejavu2-cli.

This module contains client initialization and query functions for
various LLM providers: OpenAI, Anthropic, Google, and local Ollama models.
"""
import os
import logging
import click
from typing import Dict, Any, List, Optional

# Import LLM provider libraries
from anthropic import Anthropic
from openai import OpenAI
import google.generativeai as genai

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
        'GOOGLE_API_KEY': os.environ.get('GOOGLE_API_KEY', '')
    }
    
    # Log which keys are available (without revealing actual keys)
    available_keys = [name for name, key in api_keys.items() if key]
    missing_keys = [name for name, key in api_keys.items() if not key]
    
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

    # Local Ollama client doesn't require API key validation
    try:
        clients['ollama'] = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
    except Exception as e:
        logger.error(f"Ollama client error: {e}")
        clients['ollama'] = None
    
    return clients

# Query functions
def query_anthropic(
    client: Anthropic,
    query_text: str,
    systemprompt: str,
    model: str,
    temperature: float,
    max_tokens: int
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
        
        message = client.messages.create(
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": query_text}],
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
    max_tokens: int
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
        
    Returns:
        The model's response as a string
        
    Raises:
        ValueError: If the OpenAI API key is missing or invalid
        Exception: If the API request fails
    """
    logger.debug(f'OpenAI query: model={model}, temperature={temperature}, max_tokens={max_tokens}')
    try:
        # Check if we have a valid client
        if client is None:
            raise ValueError("OpenAI client initialization failed. Check API key validity.")
            
        # o1* Models and o3* models - different prompt format and parameters
        if model.startswith(('o1', 'o3')):
            # o1 and o3 models use max_completion_tokens instead of max_tokens
            # and don't accept temperature parameter
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": system},
                    {"role": "assistant", "content": "I have read and I understand this."},
                    {"role": "user", "content": query}
                ],
                max_completion_tokens=max_tokens,
            )
        # *gpt* Models - standard format
        else:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": query}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                n=1, stop=''
            )
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
    max_tokens: int
) -> str:
    """
    Send a query to a local LLaMA-based model via the Ollama server.
    
    Args:
        client: OpenAI client configured for Ollama
        query_text: The user's query or prompt
        systemprompt: System prompt that guides the model's behavior
        model: The LLaMA model name to use
        temperature: Sampling temperature (higher = more random)
        max_tokens: Maximum number of tokens in the response
        
    Returns:
        The model's response as a string
        
    Raises:
        Exception: If the Ollama server is not running or returns an error
    """
    try:
        # No API key check needed for local Ollama server, but check that it's running
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": systemprompt},
                {"role": "user", "content": query_text}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        # Provide more helpful error message for common Ollama connection issues
        if "connection refused" in str(e).lower():
            click.echo(f"Ollama server not running on localhost:11434", err=True)
        else:
            click.echo(f"{model} query failed: {e}", err=True)
        raise

def query_gemini(
    query: str,
    system: str,
    model: str,
    temperature: float,
    max_tokens: int,
    api_key: str
) -> str:
    """
    Send a query to the Google Gemini API and return the response.
    
    Args:
        query: The user's query or prompt
        system: System prompt that guides the model's behavior
        model: The Gemini model name to use
        temperature: Sampling temperature (higher = more random)
        max_tokens: Maximum number of tokens in the response
        api_key: Google API key
        
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
        # Configure the Gemini API with the key
        genai.configure(api_key=api_key)
        
        # Create generation config
        gen_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        # Format prompt according to Gemini's requirements
        prompt = f"<s>\n{system}\n</s>\n\n{query}"
        
        # Create and call model
        model_obj = genai.GenerativeModel(model, generation_config=gen_config)
        response = model_obj.generate_content(prompt)
        
        # Check if we got a valid response
        if response and response.text:
            return response.text
        raise Exception(f"Model {model} is not supported or did not return a result.")
    except ValueError as ve:
        # Handle validation errors from the API
        if "api_key" in str(ve).lower():
            raise ValueError(f"Invalid Google API key: {ve}")
        raise ve
    except Exception as e:
        # Log error and provide useful information
        error_msg = f"{model} query failed: {e}"
        logger.error(error_msg)
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
    logger.debug(f"Query parameters: temperature={temperature}, max_tokens={max_tokens}")
    
    # Check if conversation history is included
    if messages:
        logger.debug(f"Including {len(messages)} previous messages from conversation history")
    
    # Ensure max_tokens doesn't exceed model limit
    original_max_tokens = max_tokens
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
    if systemprompt != original_systemprompt:
        logger.debug("Applied spacetime replacements to system prompt")

    # Determine provider based on model name
    try:
        if model.startswith(('gpt', 'chatgpt', 'o1', 'o3')):
            logger.debug(f"Routing to OpenAI API with model: {model}")
            client = clients.get('openai')
            if client is None:
                logger.error("OpenAI client not available, API key might be missing")
                raise ValueError("OpenAI client not available. Please check API key.")
                
            return query_openai(
                client, query_text, systemprompt, model, 
                temperature, max_tokens
            )
            
        elif model.startswith('claude'):
            logger.debug(f"Routing to Anthropic API with model: {model}")
            client = clients.get('anthropic')
            if client is None:
                logger.error("Anthropic client not available, API key might be missing")
                raise ValueError("Anthropic client not available. Please check API key.")
                
            return query_anthropic(
                client, query_text, systemprompt, model, 
                temperature, max_tokens
            )
            
        elif model.startswith('llama') or model.startswith('nemo'):
            logger.debug(f"Routing to local Ollama with model: {model}")
            client = clients.get('ollama')
            if client is None:
                logger.error("Ollama client not available, local server might not be running")
                raise ValueError("Ollama client not available. Is the Ollama server running?")
                
            return query_llama(
                client, query_text, systemprompt, model, 
                temperature, max_tokens
            )
            
        elif model.startswith('gemini'):
            logger.debug(f"Routing to Google Gemini API with model: {model}")
            if not api_keys.get('GOOGLE_API_KEY'):
                logger.error("Google API key not available")
                raise ValueError("Google API key not available. Please check environment variables.")
                
            return query_gemini(
                query_text, systemprompt, model, temperature, max_tokens, 
                api_keys['GOOGLE_API_KEY']
            )
            
        else:
            logger.error(f"Unknown model '{model}', cannot route query")
            raise ValueError(f"Unknown model '{model}'. Check Models.json for available models.")
            
    except Exception as e:
        logger.error(f"Error querying model {model}: {str(e)}", exc_info=True)
        raise