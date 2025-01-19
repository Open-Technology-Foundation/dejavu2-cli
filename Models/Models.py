import json
import sys
from pathlib import Path
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_canonical_model(model_name: str) -> Optional[Dict[str, Any]]:
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
