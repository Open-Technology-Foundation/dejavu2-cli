#!/usr/bin/env python3
"""
Models.py - Root module for model management in dejavu2-cli

This module provides functions for retrieving LLM model information from Models.json,
including determining canonical model names from aliases and extracting model details.

This is the root module that mirrors functionality in Models/Models.py for simplified imports.

Functions:
    get_canonical_model: Get model details by name or alias
"""

import json
import sys
from pathlib import Path
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_canonical_model(model_name: str) -> Optional[Dict[str, Any]]:
  """
  Get model details by canonical name or alias.
  
  Searches Models.json for a matching model by direct name or by alias.
  Checks if the model is available and enabled.
  
  Args:
      model_name: The model name or alias to look up
      
  Returns:
      Dictionary containing model details if found, empty string if not available/enabled,
      or empty string if not found
      
  Raises:
      SystemExit: If Models.json cannot be found or contains invalid JSON
  """
  json_file = Path(__file__).parent / "Models.json"
  try:
    with open(json_file, 'r', encoding='utf-8') as file:
      models = json.load(file)
  except FileNotFoundError:
    logger.error(f"The file '{json_file}' was not found.")
    sys.exit(1)
  except json.JSONDecodeError:
    logger.error(f"The file '{json_file}' contains invalid JSON.")
    sys.exit(1)

  # normalize model name
  model_name = model_name.replace(' ', '').strip().lower()

  # Determine canonical name
  canonical_name = model_name if model_name in models else None

  if not canonical_name:
    # Search for alias
    for name, details in models.items():
      if details.get('alias') == model_name:
        if not details.get('available', 0):
          # always return a str val
          return ''
        if not details.get('enabled', 0):
          return ''
        canonical_name = name
        break

  if not canonical_name:
    logger.error(f"Model '{model_name}' not found.")
    return ''
  return models.get(canonical_name, {})

if __name__ == '__main__':
  model_name = "o1"  # This can be a canonical name or an alias

  model_parameters = get_canonical_model(model_name)
  if model_parameters:
    print(f"model: {model_parameters['model']}")
    for key, value in model_parameters.items():
      print(f"{key}: {value}")

  print(get_canonical_model(model_name)['model'])

#fin
