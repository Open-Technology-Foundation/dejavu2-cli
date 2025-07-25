"""
Ollama provider module for Claude-based model updates
"""

import logging
from typing import Dict, List, Any
from . import BaseProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Provider for Ollama local models"""
    
    @staticmethod
    def get_search_prompt() -> str:
        """Return the prompt for Claude to search for Ollama model information"""
        # Load current Ollama models from Models.json if available
        current_models = {}
        try:
            from pathlib import Path
            import json
            models_json_path = Path(__file__).parent.parent.parent / "Models.json"
            if models_json_path.exists():
                with open(models_json_path, 'r') as f:
                    all_models = json.load(f)
                    # Filter for Ollama models (various parents but family=ollama)
                    current_models = {
                        k: v for k, v in all_models.items() 
                        if v.get('family') == 'ollama'
                    }
        except Exception:
            # If we can't load Models.json, continue without it
            pass
        
        prompt = """Search for Ollama's current model information and return a JSON object with this exact structure:

```json
{
  "llama3.1:8b": {
    "model": "llama3.1:8b",
    "alias": "llama31",
    "parent": "Meta",
    "model_category": "LLM",
    "family": "ollama",
    "series": "llama3",
    "description": "Meta's Llama 3.1 8B model via Ollama",
    "data_cutoff_date": "2024-04",
    "url": "http://localhost:11434/api",
    "apikey": "ollama",
    "context_window": 128000,
    "max_output_tokens": 4096,
    "token_costs": "0",
    "vision": 0,
    "available": 1,
    "enabled": 0
  }
}
```

"""
        
        if current_models:
            prompt += "Here are the current Ollama models in Models.json that need to be updated with the latest information:\n\n```json\n"
            prompt += json.dumps(current_models, indent=2)
            prompt += "\n```\n\n"
            prompt += "Update these models with the latest information and add any new models that are missing.\n"
        else:
            prompt += "Search for ONLY the TOP 10-15 most popular Ollama models. Focus on major models like:\n"
            prompt += "- Llama 3.1/3.2 (8B, 70B variants)\n"
            prompt += "- Mistral/Mixtral models\n"
            prompt += "- CodeLlama variants\n"
            prompt += "- Phi-3 models\n"
            prompt += "- Gemma/Gemma2 models\n"
            prompt += "- Qwen2.5 models\n"
            prompt += "- DeepSeek Coder\n"
            prompt += "DO NOT include every variant - only the most commonly used sizes.\n"
        
        prompt += """
Include accurate information for:
- model: exact model ID for Ollama (e.g., "llama3.1:8b")
- alias: short nickname
- parent: Original model creator (Meta, Mistral, Google, Microsoft, etc.)
- family: always "ollama"
- series: model series name
- context_window: max input tokens
- max_output_tokens: max output tokens
- token_costs: always "0" (local models are free)
- data_cutoff_date: format as "YYYY-MM"
- vision: 1 if supports images, 0 if not
- url: typically "http://localhost:11434/api"
- apikey: typically "ollama" or model-specific

IMPORTANT: Limit your response to 10-15 models maximum. Focus on quality over quantity.

CRITICAL: Your response must be ONLY valid JSON starting with { and ending with }. Do not include ANY text before or after the JSON. Do not wrap in markdown code blocks. Do not include explanations."""
        
        return prompt
    
    @staticmethod
    def validate_and_format(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and format Claude's response into Models.json format"""
        # Debug logging
        logger.debug(f"Raw data type: {type(raw_data)}")
        logger.debug(f"Raw data keys: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'Not a dict'}")
        
        # If the data already appears to be in the correct format, just validate it
        if isinstance(raw_data, dict) and len(raw_data) > 0 and all(
            isinstance(v, dict) and 'model' in v 
            for v in raw_data.values()
        ):
            logger.info(f"Processing {len(raw_data)} Ollama models")
            
            # Validate each model entry
            validated_models = {}
            for model_id, model_data in raw_data.items():
                try:
                    # Ensure required fields are present
                    if not all(key in model_data for key in ['model', 'alias', 'parent']):
                        logger.warning(f"Skipping {model_id}: missing required fields")
                        continue
                    
                    # Ensure model ID matches the key
                    if model_data['model'] != model_id:
                        logger.warning(f"Model ID mismatch: {model_id} vs {model_data['model']}")
                        model_data['model'] = model_id
                    
                    # Set defaults for any missing fields
                    model_data.setdefault('model_category', 'LLM')
                    model_data.setdefault('family', 'ollama')
                    model_data.setdefault('url', 'http://localhost:11434/api')
                    model_data.setdefault('apikey', 'ollama')
                    model_data.setdefault('token_costs', '0')
                    model_data.setdefault('available', 1)
                    model_data.setdefault('enabled', 0)
                    
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
get_search_prompt = OllamaProvider.get_search_prompt
validate_and_format = OllamaProvider.validate_and_format