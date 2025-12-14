"""
Mistral provider module for Claude-based model updates
"""

import logging
from typing import Any

from . import BaseProvider

logger = logging.getLogger(__name__)


class MistralProvider(BaseProvider):
  """Provider for Mistral AI models"""

  @staticmethod
  def get_search_prompt() -> str:
    """Return the prompt for Claude to search for Mistral model information"""
    # Load current Mistral models from Models.json if available
    current_models = {}
    try:
      import json
      from pathlib import Path

      models_json_path = Path(__file__).parent.parent.parent / "Models.json"
      if models_json_path.exists():
        with open(models_json_path) as f:
          all_models = json.load(f)
          # Filter for Mistral models
          current_models = {k: v for k, v in all_models.items() if v.get("parent") == "Mistral"}
    except Exception:
      # If we can't load Models.json, continue without it
      pass

    prompt = """Search for Mistral AI's current model information and return a JSON object with this exact structure:

```json
{
  "mistral-large-latest": {
    "model": "mistral-large-latest",
    "alias": "mistrallarge",
    "parent": "Mistral",
    "model_category": "LLM",
    "family": "mistral",
    "series": "mistral",
    "description": "Mistral's most powerful model",
    "data_cutoff_date": "2024-04",
    "url": "https://api.mistral.ai/v1",
    "apikey": "MISTRAL_API_KEY",
    "context_window": 32000,
    "max_output_tokens": 8192,
    "token_costs": "$4.00/$12.00 per 1M tokens",
    "vision": 0,
    "available": 1,
    "enabled": 0
  }
}
```

"""

    if current_models:
      prompt += "Here are the current Mistral models in Models.json that need to be updated with the latest information:\n\n```json\n"
      prompt += json.dumps(current_models, indent=2)
      prompt += "\n```\n\n"
      prompt += "Update these models with the latest information and add any new models that are missing.\n"
    else:
      prompt += "Search for all current Mistral models including Mistral Large, Small, Mixtral, Codestral, and embedding models.\n"

    prompt += """
Include accurate information for:
- model: exact model ID for API calls
- alias: short nickname
- context_window: max input tokens
- max_output_tokens: max output tokens
- token_costs: format as "$INPUT/$OUTPUT per 1M tokens"
- data_cutoff_date: format as "YYYY-MM"
- vision: 1 if supports images, 0 if not

CRITICAL: Your response must be ONLY valid JSON starting with { and ending with }. Do not include ANY text before or after the JSON. Do not wrap in markdown code blocks. Do not include explanations."""

    return prompt

  @staticmethod
  def validate_and_format(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Validate and format Claude's response into Models.json format"""
    # Debug logging
    logger.debug(f"Raw data type: {type(raw_data)}")
    logger.debug(f"Raw data keys: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'Not a dict'}")

    # If the data already appears to be in the correct format, just validate it
    if isinstance(raw_data, dict) and len(raw_data) > 0 and all(isinstance(v, dict) and "model" in v for v in raw_data.values()):
      logger.info(f"Processing {len(raw_data)} Mistral models")

      # Validate each model entry
      validated_models = {}
      for model_id, model_data in raw_data.items():
        try:
          # Ensure required fields are present
          if not all(key in model_data for key in ["model", "alias", "parent"]):
            logger.warning(f"Skipping {model_id}: missing required fields")
            continue

          # Ensure model ID matches the key
          if model_data["model"] != model_id:
            logger.warning(f"Model ID mismatch: {model_id} vs {model_data['model']}")
            model_data["model"] = model_id

          # Set defaults for any missing fields
          model_data.setdefault("model_category", "LLM")
          model_data.setdefault("family", "mistral")
          model_data.setdefault("series", "mistral")
          model_data.setdefault("url", "https://api.mistral.ai/v1")
          model_data.setdefault("apikey", "MISTRAL_API_KEY")
          model_data.setdefault("available", 1)
          model_data.setdefault("enabled", 0)

          validated_models[model_id] = model_data
          logger.debug(f"Validated model: {model_id}")

        except Exception as e:
          logger.error(f"Error validating model {model_id}: {e}")
          continue

      return validated_models

    # If we got here, the format is unexpected
    logger.error("Invalid response format from Claude - expected dict of model objects")
    return {}


# Module-level functions for compatibility
get_search_prompt = MistralProvider.get_search_prompt
validate_and_format = MistralProvider.validate_and_format
