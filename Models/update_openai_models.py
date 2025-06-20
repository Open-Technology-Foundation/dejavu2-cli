#!/usr/bin/env python3
"""
Update OpenAI models in Models.json
----------------------------------
This script updates the Models.json file with the latest OpenAI model information.
It uses data from the OpenAI API and hardcoded pricing/capability information.

Usage:
  ./update_openai_models.py [--dry-run]
"""

import os
import json
import datetime
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
CACHE_DIR = Path(".cache/openai")
MODELS_JSON_PATH = Path("Models.json")
API_MODELS_PATH = CACHE_DIR / "models_api.json"
PRICING_PATH = CACHE_DIR / "pricing.json"
CONTEXT_WINDOWS_PATH = CACHE_DIR / "context_windows.json"
MAX_OUTPUT_TOKENS_PATH = CACHE_DIR / "max_output_tokens.json"

# Model categories and descriptions
MODEL_CATEGORIES = {
    "gpt": "LLM",
    "o1": "LLM",
    "o3": "LLM",
    "dall": "image",
    "tts": "tts",
    "whisper": "stt",
    "text-embedding": "embed",
    "chatgpt": "LLM",
    "babbage": "LLM",
    "davinci": "LLM",
    "omni": "moderation"
}

MODEL_DESCRIPTIONS = {
    "gpt-4o": "Latest flagship model with optimal balance of intelligence and speed",
    "gpt-4o-mini": "Affordable and intelligent small model for fast, lightweight tasks",
    "gpt-4.5-preview": "Preview version of GPT-4.5 with advanced reasoning capabilities",
    "gpt-4-turbo": "Powerful model with high reasoning capabilities at lower cost than GPT-4",
    "gpt-4": "High-intelligence flagship model for complex, multi-step tasks",
    "gpt-3.5-turbo": "Fast, cost-effective model for straightforward tasks",
    "o1": "OpenAI's most capable model for reasoning, coding, and creative tasks",
    "o1-mini": "Faster and cheaper version of O1 with strong reasoning abilities",
    "o3-mini": "Exceptionally intelligent and affordable model for general purpose use",
    "text-embedding-3-large": "Most capable embedding model for both English and non-English tasks",
    "text-embedding-3-small": "Increased performance over second generation ada embedding model",
    "text-embedding-ada-002": "Robust second-generation embedding model",
    "whisper-1": "Advanced speech-to-text model supporting multiple languages",
    "tts-1": "Text-to-speech model optimized for speed",
    "tts-1-hd": "Text-to-speech model optimized for quality",
    "dall-e-3": "Advanced image generation model with high fidelity and prompt following",
    "omni-moderation-latest": "Content moderation model with multiple categories"
}

# Data cutoff dates (YYYY-MM format)
DATA_CUTOFFS = {
    "gpt-4o": "2023-10",
    "gpt-4o-mini": "2023-10",
    "gpt-4.5-preview": "2023-10",
    "gpt-4-turbo": "2023-04",
    "gpt-4": "2023-04",
    "gpt-3.5-turbo": "2021-09",
    "o1": "2024-10",
    "o1-mini": "2023-10",
    "o3-mini": "2024-10"
}

# Vision capability
VISION_MODELS = [
    "gpt-4o", "gpt-4-turbo", "gpt-4-vision-preview", "gpt-4o-mini"
]

def load_cached_data():
    """Load cached model data from API and other sources"""
    data = {}
    
    # Load models from API
    if API_MODELS_PATH.exists():
        try:
            with open(API_MODELS_PATH, 'r') as f:
                data["api_models"] = json.load(f)
            logger.info(f"Loaded {len(data['api_models'])} models from API cache")
        except Exception as e:
            logger.error(f"Error loading API models: {e}")
            data["api_models"] = []
    else:
        logger.warning(f"{API_MODELS_PATH} not found. Run examine_openai_models.py first.")
        data["api_models"] = []
    
    # Load pricing data
    if PRICING_PATH.exists():
        try:
            with open(PRICING_PATH, 'r') as f:
                data["pricing"] = json.load(f)
            logger.info(f"Loaded pricing data for {len(data['pricing'])} models")
        except Exception as e:
            logger.error(f"Error loading pricing data: {e}")
            data["pricing"] = {}
    else:
        logger.warning(f"{PRICING_PATH} not found. Using default pricing.")
        data["pricing"] = {}
    
    # Load context windows
    if CONTEXT_WINDOWS_PATH.exists():
        try:
            with open(CONTEXT_WINDOWS_PATH, 'r') as f:
                data["context_windows"] = json.load(f)
            logger.info(f"Loaded context windows for {len(data['context_windows'])} models")
        except Exception as e:
            logger.error(f"Error loading context windows: {e}")
            data["context_windows"] = {}
    else:
        logger.warning(f"{CONTEXT_WINDOWS_PATH} not found. Using default values.")
        data["context_windows"] = {}
    
    # Load max output tokens
    if MAX_OUTPUT_TOKENS_PATH.exists():
        try:
            with open(MAX_OUTPUT_TOKENS_PATH, 'r') as f:
                data["max_output_tokens"] = json.load(f)
            logger.info(f"Loaded max output tokens for {len(data['max_output_tokens'])} models")
        except Exception as e:
            logger.error(f"Error loading max output tokens: {e}")
            data["max_output_tokens"] = {}
    else:
        logger.warning(f"{MAX_OUTPUT_TOKENS_PATH} not found. Using default values.")
        data["max_output_tokens"] = {}
    
    return data

def identify_key_models(api_models):
    """Identify key models from the API response"""
    # Convert timestamps to dates
    for model in api_models:
        if "created" in model:
            timestamp = model["created"]
            model["created_date"] = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    
    # Identify latest models (no date suffix)
    latest_models = []
    for model in api_models:
        model_id = model["id"]
        parts = model_id.split("-")
        
        # Skip models with dates in their names
        if any(part.isdigit() and len(part) >= 4 for part in parts):
            continue
        
        # Skip any models with all digit endings
        if model_id[-1].isdigit() and all(c.isdigit() for c in parts[-1]):
            continue
            
        latest_models.append(model)
    
    # Group models by family
    model_families = {}
    for model in api_models:
        model_id = model["id"]
        parts = model_id.split("-")
        
        # Determine family
        if len(parts) > 0:
            family = parts[0]
            
            # Handle special cases
            if family == "gpt" and len(parts) > 1:
                version = parts[1]
                family = f"gpt-{version}"
            
            # Handle o1, o3 etc.
            if family in ("o1", "o3") and len(parts) > 1 and parts[1] == "mini":
                family = f"{family}-mini"
        else:
            family = "other"
        
        if family not in model_families:
            model_families[family] = []
        
        model_families[family].append(model)
    
    # Find newest versions in each family
    newest_versions = {}
    for family, models in model_families.items():
        # Sort by creation date, newest first
        sorted_models = sorted(models, key=lambda x: x.get("created", 0), reverse=True)
        if sorted_models:
            newest_versions[family] = sorted_models[0]
    
    return {
        "latest": latest_models,
        "families": model_families,
        "newest": newest_versions
    }

def format_price_string(model_id, pricing_data):
    """Format price string for Models.json"""
    if model_id not in pricing_data:
        # Try base model (without version)
        base_id = model_id.split("-")[0]
        if base_id in pricing_data:
            model_id = base_id
        else:
            # Try prefix matching
            for price_id in pricing_data.keys():
                if model_id.startswith(price_id):
                    model_id = price_id
                    break
    
    if model_id in pricing_data:
        pricing = pricing_data[model_id]
        if "input" in pricing and "output" in pricing:
            if pricing["output"] > 0:
                return f"${pricing['input']}/{pricing['output']} per {pricing['input_unit']}"
            else:
                return f"${pricing['input']} per {pricing['input_unit']}"
        elif "unit" in pricing:
            prices = ", ".join([f"${pricing[size]} ({size})" for size in pricing if size != "unit"])
            return f"{prices} {pricing['unit']}"
    
    return ""

def determine_alias(model_id):
    """Determine alias for a model"""
    parts = model_id.split("-")
    
    # Handle special cases
    if model_id.startswith("gpt-4o"):
        if "mini" in model_id:
            return "gpt4omini"
        return "gpt4o"
    
    if model_id.startswith("o1") or model_id.startswith("o3"):
        if "mini" in model_id:
            return f"{parts[0]}mini"
        return parts[0]
    
    if model_id.startswith("gpt-4.5"):
        return "gpt45"
    
    if model_id.startswith("gpt-4"):
        if "turbo" in model_id:
            return "gpt4turbo"
        return "gpt4"
    
    if model_id.startswith("gpt-3.5"):
        if "turbo" in model_id and "instruct" in model_id:
            return "gpt35instruct"
        if "turbo" in model_id:
            return "gpt35"
        return "gpt35"
    
    if model_id.startswith("text-embedding"):
        if "ada" in model_id:
            return "ada2"
        if "small" in model_id:
            return "embed3small"
        if "large" in model_id:
            return "embed3large"
        
    if model_id.startswith("dall-e"):
        return model_id.replace("-", "")
    
    if model_id.startswith("whisper"):
        return model_id.replace("-", "")
    
    if model_id.startswith("tts"):
        if "hd" in model_id:
            return "tts1hd"
        return "tts1"
    
    # Default: remove hyphens and use full name
    return model_id.replace("-", "")

def determine_family_series(model_id):
    """Determine family and series for a model"""
    family = ""
    series = ""
    
    if model_id.startswith("gpt-4o") or model_id.startswith("gpt-4") or model_id.startswith("gpt-4.5"):
        family = "gpt4"
        series = "gpt4"
    elif model_id.startswith("gpt-3.5"):
        family = "gpt35"
        series = "gpt35"
    elif model_id.startswith("o1"):
        family = "o1"
        series = "o1"
    elif model_id.startswith("o3"):
        family = "o3"
        series = "o3"
    elif model_id.startswith("text-embedding-3"):
        family = "embed3"
        series = "embed3"
    elif model_id.startswith("text-embedding-ada"):
        family = "ada2"
        series = "ada2"
    elif model_id.startswith("dall-e"):
        family = "dalle"
        series = "dalle"
    elif model_id.startswith("whisper"):
        family = "whisper"
        series = "whisper"
    elif model_id.startswith("tts"):
        family = "tts"
        series = "tts"
    elif model_id.startswith("babbage") or model_id.startswith("davinci"):
        family = model_id.split("-")[0]
        series = model_id.split("-")[0]
    elif model_id.startswith("omni"):
        family = "omni"
        series = "omni"
    else:
        # Default: use first part of model ID
        parts = model_id.split("-")
        if parts:
            family = parts[0]
            series = parts[0]
    
    return family, series

def determine_category(model_id):
    """Determine category for a model"""
    for prefix, category in MODEL_CATEGORIES.items():
        if model_id.startswith(prefix):
            return category
    return "LLM"  # Default category

def determine_description(model_id):
    """Determine description for a model"""
    # Try exact match
    if model_id in MODEL_DESCRIPTIONS:
        return MODEL_DESCRIPTIONS[model_id]
    
    # Try prefix matching
    for prefix, description in MODEL_DESCRIPTIONS.items():
        if model_id.startswith(prefix):
            return description
    
    # Default description based on category
    category = determine_category(model_id)
    if category == "LLM":
        return "Language model trained with reinforcement learning"
    elif category == "image":
        return "Image generation model"
    elif category == "embed":
        return "Text embedding model"
    elif category == "tts":
        return "Text-to-speech model"
    elif category == "stt":
        return "Speech-to-text model"
    elif category == "moderation":
        return "Content moderation model"
    
    return f"OpenAI {category} model"

def determine_cutoff_date(model_id):
    """Determine data cutoff date for a model"""
    # Try exact match
    if model_id in DATA_CUTOFFS:
        return DATA_CUTOFFS[model_id]
    
    # Try prefix matching
    for prefix, cutoff in DATA_CUTOFFS.items():
        if model_id.startswith(prefix):
            return cutoff
    
    # Try to extract date from model name
    parts = model_id.split("-")
    for part in parts:
        if len(part) == 8 and part.isdigit():
            # Format YYYYMMDD as YYYY-MM
            return f"{part[:4]}-{part[4:6]}"
        if len(part) == 4 and part.isdigit():
            # Assume year only
            return f"{part}-01"
    
    # Default
    return ""

def determine_vision_capability(model_id):
    """Determine if a model has vision capability"""
    for vision_model in VISION_MODELS:
        if model_id.startswith(vision_model):
            return 1
    return 0

def update_models_json(cached_data, dry_run=False):
    """Update Models.json with OpenAI model information"""
    # Get model data from cache
    api_models = cached_data.get("api_models", [])
    pricing_data = cached_data.get("pricing", {})
    context_windows = cached_data.get("context_windows", {})
    max_output_tokens = cached_data.get("max_output_tokens", {})
    
    # Identify important models
    key_models = identify_key_models(api_models)
    
    # Read existing Models.json
    if MODELS_JSON_PATH.exists():
        try:
            with open(MODELS_JSON_PATH, 'r') as f:
                models_json = json.load(f)
            logger.info(f"Successfully read existing {MODELS_JSON_PATH}")
        except Exception as e:
            logger.error(f"Error reading {MODELS_JSON_PATH}: {e}")
            models_json = {}
    else:
        logger.warning(f"{MODELS_JSON_PATH} does not exist, creating new one")
        models_json = {}
    
    if dry_run:
        logger.info("Dry run mode - not modifying Models.json")
        
        # Show models that would be updated
        openai_models = []
        for model in api_models:
            model_id = model["id"]
            if model_id in models_json and models_json[model_id].get("parent") == "OpenAI":
                openai_models.append(model_id)
        
        logger.info(f"Would update {len(openai_models)} existing OpenAI models")
        
        # Show new models that would be added
        new_models = []
        for model in key_models["latest"]:
            model_id = model["id"]
            if model_id not in models_json:
                new_models.append(model_id)
        
        logger.info(f"Would add {len(new_models)} new OpenAI models")
        logger.info("Sample new models to add:")
        for model_id in new_models[:5]:
            logger.info(f"- {model_id}")
            
        return 0, 0
    
    # Make a backup of the current file
    backup_path = Path(f"{MODELS_JSON_PATH}.openai.backup")
    try:
        with open(backup_path, 'w') as f:
            json.dump(models_json, f, indent=2)
        logger.info(f"Created backup at {backup_path}")
    except Exception as e:
        logger.warning(f"Could not create backup: {e}")
    
    # Update or add models
    models_updated = 0
    models_added = 0
    
    # Focus on latest models first
    for model in key_models["latest"]:
        model_id = model["id"]
        
        # Skip internal models
        if model.get("owned_by") != "system":
            continue
        
        # Get context window and max output tokens
        context_window = context_windows.get(model_id)
        if not context_window:
            # Try prefix matching
            for window_id, value in context_windows.items():
                if model_id.startswith(window_id):
                    context_window = value
                    break
        
        max_tokens = max_output_tokens.get(model_id)
        if not max_tokens:
            # Try prefix matching
            for tokens_id, value in max_output_tokens.items():
                if model_id.startswith(tokens_id):
                    max_tokens = value
                    break
        
        # Determine other model properties
        family, series = determine_family_series(model_id)
        category = determine_category(model_id)
        description = determine_description(model_id)
        cutoff_date = determine_cutoff_date(model_id)
        vision = determine_vision_capability(model_id)
        price = format_price_string(model_id, pricing_data)
        alias = determine_alias(model_id)
        
        # Create model entry
        model_json = {
            "model": model_id,
            "alias": alias,
            "parent": "OpenAI",
            "model_category": category,
            "family": family,
            "series": series,
            "description": description,
            "data_cutoff_date": cutoff_date,
            "url": "https://api.openai.com/v1",
            "apikey": "OPENAI_API_KEY",
            "context_window": context_window,
            "max_output_tokens": max_tokens,
            "token_costs": price,
            "vision": vision,
            "available": 1,
            "enabled": 0
        }
        
        # Update or add
        if model_id in models_json:
            # Preserve existing enabled/available state
            model_json["enabled"] = models_json[model_id].get("enabled", 0)
            model_json["available"] = models_json[model_id].get("available", 1)
            models_json[model_id] = model_json
            models_updated += 1
            logger.info(f"Updated existing model: {model_id}")
        else:
            models_json[model_id] = model_json
            models_added += 1
            logger.info(f"Added new model: {model_id}")
    
    # Write updated models.json
    with open(MODELS_JSON_PATH, 'w') as f:
        json.dump(models_json, f, indent=2)
    
    logger.info(f"Updated Models.json: {models_updated} models updated, {models_added} models added")
    return models_updated, models_added

def main():
    """Main function to update OpenAI models"""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Update OpenAI models in Models.json")
    parser.add_argument("--dry-run", action="store_true", help="Do not modify Models.json, just show what would be changed")
    args = parser.parse_args()
    
    logger.info("Starting update of OpenAI models")
    
    # Load cached data
    cached_data = load_cached_data()
    
    if not cached_data["api_models"]:
        logger.error("No model data available. Run examine_openai_models.py first.")
        return
    
    # Update Models.json
    updated, added = update_models_json(cached_data, args.dry_run)
    
    if not args.dry_run:
        logger.info(f"Finished updating OpenAI models: {updated} updated, {added} added")

if __name__ == "__main__":
    main()

#fin