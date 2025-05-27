#!/usr/bin/env python3
"""
Model handling for dejavu2-cli.

This module handles loading and selecting LLM models from Models.json,
as well as listing and displaying model information.
"""
import os
import sys
import json
import click
import logging
from typing import Dict, List, Any, Optional, Tuple

# Import custom exceptions
from errors import ConfigurationError, ModelError

# Configure module logger
logger = logging.getLogger(__name__)

def list_available_canonical_models(json_file: str) -> List[str]:
    """
    List all available model names from Models.json.
    
    Args:
        json_file: Path to the Models.json file
        
    Returns:
        List of available model names sorted alphabetically
        
    Raises:
        ConfigurationError: If the models file cannot be found or parsed
    """
    logger.debug(f"Loading models from: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            models = json.load(file)
            logger.debug(f"Successfully loaded {len(models)} models from file")
    except FileNotFoundError:
        error_msg = f"Models file not found: {json_file}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in models file '{json_file}': {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)
    except Exception as e:
        error_msg = f"Error loading models file '{json_file}': {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)
        
    # Extract canonical model names where 'available' is not 0
    canonical_names = [
        name for name, details in models.items()
        if details.get('available') != 0
    ]
    
    # Sort the canonical model names
    canonical_names.sort()
    
    logger.debug(f"Found {len(canonical_names)} available models out of {len(models)} total")
    return canonical_names

def list_available_canonical_models_with_details(json_file: str) -> Dict[str, Any]:
    """
    Get a dictionary of all available models with their complete details.
    
    Args:
        json_file: Path to the Models.json file
        
    Returns:
        Dictionary mapping model names to their complete details for available models
        
    Raises:
        ConfigurationError: If the models file cannot be found or parsed
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            models = json.load(file)
    except FileNotFoundError:
        error_msg = f"Models file not found: {json_file}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in models file '{json_file}': {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)
        
    # Extract models where 'available' is greater than 0
    available_models = {
        name: details for name, details in models.items()
        if details.get('available') > 0
    }
    return available_models

def get_canonical_model(model_name: str, json_file: str) -> tuple[str, Dict[str, Any]]:
    """
    Get canonical model name and load model parameters.
    
    Searches Models.json for either an exact match on model name or a match
    on the alias field. When found, loads parameters.
    
    Args:
        model_name: The model name or alias to look up
        json_file: Path to the Models.json file
        
    Returns:
        Tuple of (canonical_model_name, model_parameters)
        
    Raises:
        ConfigurationError: If Models.json cannot be found or contains invalid JSON
        ModelError: If the requested model is not found
    """
    logger.debug(f"Looking up model: '{model_name}' in {json_file}")
    model_parameters = {}
    
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            models = json.load(file)
            logger.debug(f"Successfully loaded {len(models)} models from {json_file}")
    except FileNotFoundError:
        error_msg = f"Models file not found: {json_file}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in models file '{json_file}': {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)

    # Check if the model name is a canonical name
    canonical_name = None
    if model_name in models:
        canonical_name = model_name
        logger.debug(f"Found exact match for model name: '{model_name}'")
    else:
        logger.debug(f"Model '{model_name}' not found directly, searching aliases")
        # Search through aliases
        for name, details in models.items():
            if details.get('alias') == model_name:
                logger.debug(f"Found alias match: '{model_name}' → '{name}'")
                
                if details.get('available') == 0:
                    error_msg = f"Alias '{model_name}' was found but is unavailable"
                    logger.warning(error_msg)
                    click.echo(f"Warning: {error_msg}", err=True)
                    return None, {}
                    
                if details.get('enabled') == 0:
                    error_msg = f"Alias '{model_name}' was found but is not enabled"
                    logger.warning(error_msg)
                    click.echo(f"Warning: {error_msg}", err=True)
                    return None, {}
                    
                canonical_name = name
                break

    if not canonical_name:
        # Model name not found
        error_msg = f"Model '{model_name}' not found in models file"
        logger.warning(error_msg)
        raise ModelError(error_msg)

    # Initialize model_parameters from Models.json - include all model information
    model_info = models.get(canonical_name, {})
    logger.debug(f"Found model info for '{canonical_name}' with {len(model_info)} parameters")
    
    # Essential fields that must be present
    required_fields = [
        'model',
        'series',
        'url',
        'apikey',
        'context_window',
        'max_output_tokens',
        'available',
        'enabled'
    ]
    
    # Copy all model info to model_parameters
    for field, value in model_info.items():
        model_parameters[field] = value
    
    # Verify required fields exist (set to None if missing)
    missing_fields = []
    for field in required_fields:
        if field not in model_parameters:
            model_parameters[field] = None
            missing_fields.append(field)
    
    if missing_fields:
        logger.warning(f"Model '{canonical_name}' is missing required fields: {', '.join(missing_fields)}")

    logger.info(f"Selected model: {canonical_name} ({model_parameters.get('provider', 'Unknown provider')})")
    return canonical_name, model_parameters

def list_models(json_file: str, details: bool = False) -> None:
    """
    List all available LLM models as defined in Models.json.
    
    Args:
        json_file: Path to the Models.json file
        details: If True, shows detailed information about each model.
                If False, shows only the model names.
    """
    if details:
        models = list_available_canonical_models_with_details(json_file)
        for name, details in sorted(models.items()):
            click.echo(f"Model: {name}")
            for key, value in details.items():
                click.echo(f"  {key}: {value}")
            click.echo()
    else:
        models = list_available_canonical_models(json_file)
        for name in models:
            click.echo(f"{name}")