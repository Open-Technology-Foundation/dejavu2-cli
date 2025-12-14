"""
Anthropic provider module for Claude-based model updates
"""

import logging
from typing import Any

from . import BaseProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
  """Provider for Anthropic Claude models"""

  @staticmethod
  def get_search_prompt() -> str:
    """Return the prompt for Claude to search for Anthropic model information"""
    prompt = """Search for ALL current Anthropic Claude models from their official documentation and API references. Return a complete JSON object with this exact structure for EACH model:

```json
{
  "model-id-here": {
    "model": "model-id-here",
    "alias": "short-alias",
    "parent": "Anthropic",
    "model_category": "LLM",
    "family": "anthropic",
    "series": "claude3",
    "description": "Model description",
    "data_cutoff_date": "YYYY-MM",
    "url": "https://api.anthropic.com/v1",
    "apikey": "ANTHROPIC_API_KEY",
    "context_window": 200000,
    "max_output_tokens": 8192,
    "token_costs": "$X.XX/$Y.YY",
    "vision": 1,
    "available": 1,
    "enabled": 0
  }
}
```

Include ALL current Anthropic models:
- All Claude 3.5 models (Sonnet, Haiku, etc.)
- All Claude 3 models (Opus, Sonnet, Haiku)
- All Claude 4 models (Opus 4, Sonnet 4)
- Both "latest" versions and dated versions (e.g., claude-3-5-sonnet-latest AND claude-3-5-sonnet-20241022)

For each model provide:
- model: exact model ID for API calls
- alias: short memorable nickname (e.g., "sonnet35" for claude-3-5-sonnet-latest)
- context_window: maximum input tokens
- max_output_tokens: maximum output tokens
- token_costs: format as "$INPUT_COST/$OUTPUT_COST" per million tokens
- data_cutoff_date: training data cutoff in "YYYY-MM" format
- vision: 1 if supports image inputs, 0 if text-only

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
      logger.info(f"Processing {len(raw_data)} Anthropic models")

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
          model_data.setdefault("family", "anthropic")
          model_data.setdefault("series", "claude3")
          model_data.setdefault("url", "https://api.anthropic.com/v1")
          model_data.setdefault("apikey", "ANTHROPIC_API_KEY")
          model_data.setdefault("available", 1)
          model_data.setdefault("enabled", 0)
          model_data.setdefault("vision", 1 if "claude-3" in model_id else 0)

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
get_search_prompt = AnthropicProvider.get_search_prompt
validate_and_format = AnthropicProvider.validate_and_format
