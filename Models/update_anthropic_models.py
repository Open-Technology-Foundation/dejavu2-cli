#!/usr/bin/env python3
"""
Update Anthropic models in Models.json
-------------------------------------
This script updates the Models.json file with the latest Anthropic model information.
It uses a combination of hardcoded data from get-models-info.md and web scraping
to obtain the most up-to-date model information.

Usage:
  ./update_anthropic_models.py

Requirements:
  - requests

The script performs the following:
1. Downloads Anthropic's documentation (with caching)
2. Updates or adds latest "-latest" models
3. Adds versioned models with timestamps
4. Sets appropriate defaults for new models (available=1, enabled=0)
5. Preserves existing settings for models already in Models.json
"""

import os
import json
import requests
import re
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directory structure
CACHE_DIR = Path(".cache/anthropic")
MODELS_JSON_PATH = Path("Models.json")

# URLs to fetch data from
URLS = {
  "models_list": "https://docs.anthropic.com/en/api/models-list",
  "models_details": "https://docs.anthropic.com/en/docs/about-claude/models/all-models"
}

# Hardcoded latest model information from get-models-info.md
LATEST_MODELS = {
  "claude-3-7-sonnet-latest": {
  "model": "claude-3-7-sonnet-latest",
  "alias": "sonnet",
  "family": "claude3",
  "description": "Highest level of intelligence and capability with toggleable extended thinking",
  "context_window": 200000,
  "max_output_tokens": 128000,
  "token_costs": "$3.00/$15.00",
  "data_cutoff_date": "2024-10",
  "vision": 1
  },
  "claude-3-5-sonnet-latest": {
  "model": "claude-3-5-sonnet-latest",
  "alias": "sonnet35",
  "family": "claude3",
  "description": "Claude 3.5 Sonnet with extended 8K tokens output",
  "context_window": 200000,
  "max_output_tokens": 8192,
  "token_costs": "$3.00/$15.00",
  "data_cutoff_date": "2024-04",
  "vision": 1
  },
  "claude-3-5-haiku-latest": {
  "model": "claude-3-5-haiku-latest",
  "alias": "haiku",
  "family": "claude3",
  "description": "Claude 3.5 Haiku. Most basic Claude model. Very fast, not always very smart.",
  "context_window": 200000,
  "max_output_tokens": 4000,
  "token_costs": "$1.00/$5.00",
  "data_cutoff_date": "2024-07",
  "vision": 1
  },
  "claude-3-opus-latest": {
  "model": "claude-3-opus-latest",
  "alias": "opus",
  "family": "claude3",
  "description": "Claude 3 Opus. Most powerful Claude model.",
  "context_window": 200000,
  "max_output_tokens": 4096,
  "token_costs": "$15.00/$75.00",
  "data_cutoff_date": "2024-02",
  "vision": 1
  },
  "claude-3-sonnet-latest": {
  "model": "claude-3-sonnet-latest",
  "alias": "sonnet3",
  "family": "claude3",
  "description": "Claude 3 Sonnet. Good balance of intelligence and speed.",
  "context_window": 200000,
  "max_output_tokens": 4096,
  "token_costs": "$3.00/$15.00",
  "data_cutoff_date": "2024-02",
  "vision": 1
  },
  "claude-3-haiku-latest": {
  "model": "claude-3-haiku-latest",
  "alias": "haiku3",
  "family": "claude3",
  "description": "Claude 3 Haiku. Fastest Claude model.",
  "context_window": 200000,
  "max_output_tokens": 4096,
  "token_costs": "$0.25/$1.25",
  "data_cutoff_date": "2024-02",
  "vision": 1
  }
}

# Hardcoded versioned models from API example
VERSIONED_MODELS = [
  {
  "id": "claude-3-7-sonnet-20250219",
  "created_at": "2025-02-24",
  "display_name": "Claude 3.7 Sonnet",
  "base_model": "claude-3-7-sonnet-latest"
  },
  {
  "id": "claude-3-5-sonnet-20241022", 
  "created_at": "2024-10-22",
  "display_name": "Claude 3.5 Sonnet (New)",
  "base_model": "claude-3-5-sonnet-latest"
  },
  {
  "id": "claude-3-5-haiku-20241022",
  "created_at": "2024-10-22",
  "display_name": "Claude 3.5 Haiku",
  "base_model": "claude-3-5-haiku-latest"
  },
  {
  "id": "claude-3-5-sonnet-20240620",
  "created_at": "2024-06-20",
  "display_name": "Claude 3.5 Sonnet (Old)",
  "base_model": "claude-3-5-sonnet-latest"
  },
  {
  "id": "claude-3-haiku-20240307",
  "created_at": "2024-03-07",
  "display_name": "Claude 3 Haiku",
  "base_model": "claude-3-haiku-latest"
  },
  {
  "id": "claude-3-opus-20240229",
  "created_at": "2024-02-29",
  "display_name": "Claude 3 Opus",
  "base_model": "claude-3-opus-latest"
  },
  {
  "id": "claude-3-sonnet-20240229",
  "created_at": "2024-02-29",
  "display_name": "Claude 3 Sonnet",
  "base_model": "claude-3-sonnet-latest"
  },
  {
  "id": "claude-2.1",
  "created_at": "2023-11-21",
  "display_name": "Claude 2.1",
  "base_model": None
  },
  {
  "id": "claude-2.0",
  "created_at": "2023-07-11",
  "display_name": "Claude 2.0",
  "base_model": None
  }
]

def ensure_cache_dir():
  """Ensure the cache directory exists"""
  os.makedirs(CACHE_DIR, exist_ok=True)
  logger.info(f"Cache directory ensured: {CACHE_DIR}")

def download_content():
  """Download content from URLs with caching"""
  result = {}
  for name, url in URLS.items():
    cache_path = CACHE_DIR / f"{name}.html"
    
    # Download fresh content
    logger.info(f"Downloading {url}")
    try:
      response = requests.get(url)
      response.raise_for_status()
      content = response.text
      
      # Save to cache
      with open(cache_path, 'w', encoding='utf-8') as f:
        f.write(content)
      
      result[name] = content
      logger.info(f"Downloaded and cached {name}")
    except Exception as e:
      logger.error(f"Error downloading {url}: {e}")
      
      # Try to use cached version if available
      if cache_path.exists():
        logger.info(f"Using cached version of {name}")
        with open(cache_path, 'r', encoding='utf-8') as f:
          result[name] = f.read()
      else:
        logger.error(f"No cached version available for {name}")
        result[name] = ""
  
  return result

def extract_latest_models_from_web(content):
  """Attempt to extract latest model information from web content"""
  # This function would try to extract information from the documentation
  # Currently we rely on hardcoded data, but this could be enhanced later
  logger.info("Using hardcoded latest model information")
  return []

def extract_versioned_models_from_web(content):
  """Attempt to extract versioned model information from web content"""
  # Try to find the SyncPage pattern in the models list
  model_list_pattern = r"SyncPage\[ModelInfo\]\(data=\[(.*?)\], has_more="
  match = re.search(model_list_pattern, content["models_list"], re.DOTALL)
  
  if not match:
    logger.warning("Could not find model list in content, using hardcoded versioned models")
    return VERSIONED_MODELS
  
  # Extract model IDs and creation dates
  model_infos = match.group(1)
  model_pattern = r"ModelInfo\(id='([^']+)', created_at=datetime\.datetime\((\d+), (\d+), (\d+)[^)]*\), display_name='([^']+)'"
  models = []
  
  for match in re.finditer(model_pattern, model_infos):
    model_id = match.group(1)
    year = int(match.group(2))
    month = int(match.group(3))
    day = int(match.group(4))
    display_name = match.group(5)
    
    created_date = f"{year}-{month:02d}-{day:02d}"
    
    # Find base model
    base_model = None
    for latest_id in LATEST_MODELS.keys():
      if model_id.startswith(latest_id.replace("-latest", "")):
        base_model = latest_id
        break
    
    models.append({
      "id": model_id,
      "created_at": created_date,
      "display_name": display_name,
      "base_model": base_model
    })
  
  if models:
    logger.info(f"Extracted {len(models)} versioned models from web content")
    return models
  else:
    logger.warning("Could not extract versioned models, using hardcoded data")
    return VERSIONED_MODELS

def update_models_json(web_content):
  """Update the Models.json file with the latest Anthropic model information"""
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
  
  # Make a backup
  backup_path = Path(f"{MODELS_JSON_PATH}.backup")
  try:
    with open(backup_path, 'w') as f:
      json.dump(models_json, f, indent=2)
    logger.info(f"Created backup at {backup_path}")
  except Exception as e:
    logger.warning(f"Could not create backup: {e}")
  
  # Update or add latest models
  models_updated = 0
  models_added = 0
  
  # First update latest models
  for model_id, model_data in LATEST_MODELS.items():
    # Create complete model entry
    model_json = {
      "model": model_id,
      "alias": model_data["alias"],
      "parent": "Anthropic",
      "model_category": "LLM",
      "family": model_data["family"],
      "series": model_data["family"],
      "description": model_data["description"],
      "training_data": model_data["data_cutoff_date"],
      "data_cutoff_date": model_data["data_cutoff_date"],
      "url": "https://api.anthropic.com/v1",
      "apikey": "ANTHROPIC_API_KEY",
      "context_window": model_data["context_window"],
      "max_output_tokens": model_data["max_output_tokens"],
      "token_costs": model_data["token_costs"],
      "vision": model_data["vision"],
      "available": 1,
      "enabled": 0
    }
    
    if model_id in models_json:
      # Update existing model but preserve enabled/available state
      model_json["enabled"] = models_json[model_id].get("enabled", 0)
      model_json["available"] = models_json[model_id].get("available", 1)
      models_json[model_id] = model_json
      models_updated += 1
      logger.info(f"Updated existing model: {model_id}")
    else:
      # Add new model
      models_json[model_id] = model_json
      models_added += 1
      logger.info(f"Added new model: {model_id}")
  
  # Try to get versioned models from web content
  versioned_models = extract_versioned_models_from_web(web_content)
  
  # Add versioned models
  for model_info in versioned_models:
    model_id = model_info["id"]
    
    # Skip if already in the JSON
    if model_id in models_json:
      continue
    
    # Find the base model data
    base_data = None
    if model_info["base_model"] and model_info["base_model"] in LATEST_MODELS:
      base_data = LATEST_MODELS[model_info["base_model"]]
    
    # For older models without a base
    if not base_data:
      # This is for claude-2.x or other old models
      if "claude-2" in model_id:
        base_data = {
          "family": "claude2",
          "context_window": 100000,
          "max_output_tokens": 4096,
          "token_costs": "$0.80/$2.40",
          "data_cutoff_date": "2023-01",
          "vision": 0
        }
      else:
        # Generic fallback for unknown models
        base_data = next(iter(LATEST_MODELS.values()))
    
    # Determine model family
    family_parts = model_id.split("-")
    if len(family_parts) >= 2:
      if "." in family_parts[1]:  # For claude-2.1, etc.
        family = f"claude{family_parts[1].replace('.', '')}"
      else:  # For claude-3-something
        family = f"claude{family_parts[1]}"
        if len(family_parts) >= 3 and family_parts[2].isdigit() is False:
          family += family_parts[2]  # Include subfamily like claude35
    else:
      family = "claude"
    
    # Determine alias - use version number if possible
    if model_id.endswith(tuple("0123456789")):
      # For dated versions, use the date
      alias = model_id.split("-")[-1]
    else:
      # Try to extract model type
      for model_type in ["opus", "sonnet", "haiku"]:
        if model_type in model_id:
          alias = model_type
          break
      else:
        # Default to last part of the ID
        alias = model_id.split("-")[-1]
    
    # Create model entry
    model_json = {
      "model": model_id,
      "alias": alias,
      "parent": "Anthropic",
      "model_category": "LLM",
      "family": base_data["family"] if "family" in base_data else family,
      "series": base_data["family"] if "family" in base_data else family,
      "description": model_info["display_name"],
      "training_data": base_data["data_cutoff_date"],
      "data_cutoff_date": base_data["data_cutoff_date"],
      "url": "https://api.anthropic.com/v1",
      "apikey": "ANTHROPIC_API_KEY",
      "context_window": base_data["context_window"],
      "max_output_tokens": base_data["max_output_tokens"],
      "token_costs": base_data["token_costs"],
      "vision": base_data["vision"],
      "available": 1,
      "enabled": 0
    }
    
    models_json[model_id] = model_json
    models_added += 1
    logger.info(f"Added versioned model: {model_id}")
  
  # Write updated models.json
  with open(MODELS_JSON_PATH, 'w') as f:
    json.dump(models_json, f, indent=2)
  
  logger.info(f"Updated Models.json: {models_updated} models updated, {models_added} models added")
  return models_updated, models_added

def main():
  """Main function to update Anthropic models"""
  # Parse arguments 
  parser = argparse.ArgumentParser(description='Update Anthropic models in Models.json')
  parser.add_argument('-s', '--skip-download', action='store_true', help='Skip downloading new content and use cached content only')
  parser.add_argument('-n', '--dry-run', action='store_true', help='Do not modify Models.json, just show what would be changed')
  args = parser.parse_args()
  
  logger.info("Starting update of Anthropic models")
  
  # Ensure cache directory exists
  ensure_cache_dir()
  
  if args.skip_download:
    logger.info("Skipping download, using cached content only")
    web_content = {}
    for name in URLS.keys():
      cache_path = CACHE_DIR / f"{name}.html"
      if cache_path.exists():
        with open(cache_path, 'r', encoding='utf-8') as f:
          web_content[name] = f.read()
        logger.info(f"Using cached {name}")
      else:
        logger.warning(f"No cached content for {name}")
        web_content[name] = ""
  else:
    # Download content
    web_content = download_content()
  
  if args.dry_run:
    logger.info("Dry run - not modifying Models.json")
    logger.info("Would update the following models:")
    for model_id in LATEST_MODELS.keys():
      logger.info(f"- {model_id}")
    logger.info("Would add the following versioned models if not present:")
    for model in VERSIONED_MODELS:
      logger.info(f"- {model['id']}")
  else:
    # Update Models.json
    updated, added = update_models_json(web_content)
    
    logger.info(f"Finished updating Anthropic models: {updated} updated, {added} added")
    
    # Some models might need manual review
    logger.info("\nThe following models have been updated with default values but may need manual review:")
    for model in VERSIONED_MODELS:
      if model["base_model"] is None:
        logger.info(f"- {model['id']} (no base model mapping, using default values)")

if __name__ == "__main__":
  main()

#fin
