"""
OpenAI provider module for Claude-based model updates
"""

import logging
from typing import Any

from . import BaseProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
  """Provider for OpenAI models"""

  @staticmethod
  def get_search_prompt() -> str:
    """Return the prompt for Claude to search for OpenAI model information"""
    # Load current OpenAI models from Models.json if available
    current_models = {}
    try:
      import json
      from pathlib import Path

      models_json_path = Path(__file__).parent.parent.parent / "Models.json"
      if models_json_path.exists():
        with open(models_json_path) as f:
          all_models = json.load(f)
          # Filter for OpenAI models
          current_models = {k: v for k, v in all_models.items() if v.get("parent") == "OpenAI"}
    except Exception:
      # If we can't load Models.json, continue without it
      pass

    prompt = """Search for OpenAI's latest model information and return a JSON object with this exact structure:

```json
{
  "gpt-4o": {
    "model": "gpt-4o",
    "alias": "gpt4o",
    "parent": "OpenAI",
    "model_category": "LLM",
    "family": "gpt4",
    "series": "gpt4",
    "description": "Latest flagship model with optimal balance of intelligence and speed",
    "data_cutoff_date": "2023-10",
    "url": "https://api.openai.com/v1",
    "apikey": "OPENAI_API_KEY",
    "context_window": 128000,
    "max_output_tokens": 16384,
    "token_costs": "$2.50/$10.00 per 1M tokens",
    "vision": 1,
    "available": 1,
    "enabled": 0
  }
}
```

"""

    if current_models:
      prompt += "Here are the current OpenAI models in Models.json that need to be updated with the latest information:\n\n```json\n"
      prompt += json.dumps(current_models, indent=2)
      prompt += "\n```\n\n"
      prompt += "Update these models with the latest information and add any new models that are missing.\n"
    else:
      prompt += "Search for all current OpenAI models including GPT-4o, GPT-4, GPT-3.5, O1/O3, embeddings, DALL-E, Whisper, and TTS models.\n"

    prompt += """
Include accurate information for:
- model: exact model ID for API calls
- alias: short nickname
- model_category: LLM, embed, image, tts, stt, or moderation
- context_window: max input tokens
- max_output_tokens: max output tokens (null for non-LLM models)
- token_costs: format as "$INPUT/$OUTPUT per 1M tokens" for LLMs, appropriate pricing for others
- data_cutoff_date: format as "YYYY-MM"
- vision: 1 if supports images, 0 if not

CRITICAL: Your response must be ONLY valid JSON starting with { and ending with }. Do not include ANY text before or after the JSON. Do not wrap in markdown code blocks. Do not include explanations."""

    return prompt

  @staticmethod
  def validate_and_format(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Validate and format Claude's response into Models.json format"""
    # If the data already appears to be in the correct format, just validate it
    if isinstance(raw_data, dict) and all(isinstance(v, dict) and "model" in v for v in raw_data.values()):
      logger.info(f"Processing {len(raw_data)} OpenAI models")

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
          model_data.setdefault("url", "https://api.openai.com/v1")
          model_data.setdefault("apikey", "OPENAI_API_KEY")
          model_data.setdefault("available", 1)
          model_data.setdefault("enabled", 0)

          # Determine family and series if not provided
          if "family" not in model_data or "series" not in model_data:
            family, series = OpenAIProvider._determine_family_series(model_id)
            model_data.setdefault("family", family)
            model_data.setdefault("series", series)

          validated_models[model_id] = model_data
          logger.debug(f"Validated model: {model_id}")

        except Exception as e:
          logger.error(f"Error validating model {model_id}: {e}")
          continue

      return validated_models

    # If we got here, the format is unexpected
    logger.error("Invalid response format from Claude - expected dict of model objects")
    return {}

  @staticmethod
  def _determine_family_series(model_id: str) -> tuple:
    """Determine family and series for OpenAI models"""
    if model_id.startswith("gpt-4o"):
      return "gpt4o", "gpt4o"
    elif model_id.startswith("gpt-4.5"):
      return "gpt45", "gpt45"
    elif model_id.startswith("gpt-4"):
      return "gpt4", "gpt4"
    elif model_id.startswith("gpt-3.5"):
      return "gpt35", "gpt35"
    elif model_id.startswith("o1"):
      return "o1", "o1"
    elif model_id.startswith("o3"):
      return "o3", "o3"
    elif model_id.startswith("text-embedding-3"):
      return "embed3", "embed3"
    elif model_id.startswith("text-embedding-ada"):
      return "ada", "ada"
    elif model_id.startswith("dall-e"):
      return "dalle", "dalle"
    elif model_id.startswith("whisper"):
      return "whisper", "whisper"
    elif model_id.startswith("tts"):
      return "tts", "tts"
    else:
      base = model_id.split("-")[0]
      return base, base

  @staticmethod
  def _generate_alias(model_id: str) -> str:
    """Generate a short alias for OpenAI models"""
    if model_id == "gpt-4o":
      return "gpt4o"
    elif model_id == "gpt-4o-mini":
      return "gpt4omini"
    elif model_id == "gpt-4.5-preview":
      return "gpt45"
    elif model_id == "gpt-4-turbo":
      return "gpt4turbo"
    elif model_id == "gpt-4":
      return "gpt4"
    elif model_id == "gpt-3.5-turbo":
      return "gpt35"
    elif model_id == "o1":
      return "o1"
    elif model_id == "o1-mini":
      return "o1mini"
    elif model_id == "o3":
      return "o3"
    elif model_id == "o3-mini":
      return "o3mini"
    elif "embedding" in model_id:
      if "large" in model_id:
        return "embed3large"
      elif "small" in model_id:
        return "embed3small"
      elif "ada" in model_id:
        return "ada2"
    elif model_id.startswith("dall-e"):
      return model_id.replace("-", "")
    elif model_id.startswith("whisper"):
      return "whisper"
    elif model_id.startswith("tts"):
      if "hd" in model_id:
        return "ttshd"
      return "tts"

    # Default: use model ID without hyphens
    return model_id.replace("-", "")

  @staticmethod
  def _format_special_pricing(model: dict[str, Any]) -> str:
    """Format pricing for non-LLM models"""
    model_category = model.get("model_category", "")

    if model_category == "image":
      # DALL-E pricing by resolution
      return model.get("pricing_info", "$0.02 per image")
    elif model_category == "tts":
      # TTS pricing per million characters
      return model.get("pricing_info", "$15.00 per 1M characters")
    elif model_category == "stt":
      # Whisper pricing per minute
      return model.get("pricing_info", "$0.006 per minute")
    else:
      # Default format
      input_price = model.get("input_price", 0)
      return f"${input_price:.3f} per request"


# Module-level functions for compatibility
get_search_prompt = OpenAIProvider.get_search_prompt
validate_and_format = OpenAIProvider.validate_and_format
