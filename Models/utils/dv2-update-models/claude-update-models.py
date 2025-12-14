#!/usr/bin/env python3
"""
Claude-based Models.json Update System
-------------------------------------
This script uses the claude CLI with --print flag to perform comprehensive
web searches and update Models.json with the latest LLM model information
from major providers.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import provider modules
from providers import anthropic, cohere, google, mistral, ollama, openai

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
# Resolve symlinks to find the actual script location
script_path = Path(__file__).resolve()
MODELS_JSON_PATH = script_path.parent.parent.parent / "Models.json"
# Use XDG cache directory or fallback to ~/.cache
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "dv2-models-update"
CACHE_EXPIRY_HOURS = 24

# Provider registry
PROVIDERS = {"anthropic": anthropic, "openai": openai, "google": google, "mistral": mistral, "cohere": cohere, "ollama": ollama}


class ClaudeModelUpdater:
  """Main class for updating models using Claude CLI"""

  def __init__(self, dry_run: bool = False, verbose: bool = False, force: bool = False, model: str = "sonnet"):
    self.dry_run = dry_run
    self.verbose = verbose
    self.force = force
    self.model = model
    self.cache_dir = CACHE_DIR
    self.cache_dir.mkdir(parents=True, exist_ok=True)

  def query_claude(self, prompt: str, use_cache: bool = True) -> dict[str, Any]:
    """Execute claude CLI with --print flag"""
    # Generate cache key from prompt and model
    cache_key = f"{str(hash(prompt))[:16]}_{self.model}"
    cache_file = self.cache_dir / f"{cache_key}.json"

    # Check cache if enabled
    if use_cache and not self.force and cache_file.exists():
      cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
      if cache_age < timedelta(hours=CACHE_EXPIRY_HOURS):
        logger.info(f"Using cached response (age: {cache_age})")
        with open(cache_file) as f:
          return json.load(f)

    # Prepare claude command
    cmd = ["claude", prompt, "--print", "--output-format", "json"]

    # Add model parameter if not 'none'
    if self.model.lower() != "none":
      cmd.extend(["--model", self.model])

    model_info = f" (model: {self.model})" if self.model.lower() != "none" else " (no model specified)"
    logger.info(f"Querying Claude for model information{model_info}...")
    if self.verbose:
      logger.debug(f"Command: {' '.join(cmd)}")
      logger.debug(f"Prompt: {prompt[:200]}...")

    try:
      result = subprocess.run(cmd, capture_output=True, text=True, check=True)

      # Parse JSON response
      response_text = result.stdout.strip()

      # Handle case where JSON is wrapped in markdown code blocks
      if response_text.startswith("```json") and response_text.endswith("```"):
        # Extract JSON from markdown code block
        json_start = response_text.find("\n") + 1
        json_end = response_text.rfind("```")
        response_text = response_text[json_start:json_end].strip()
      elif "```json" in response_text:
        # Handle case with text before the code block
        json_start = response_text.find("```json") + 7
        json_start = response_text.find("\n", json_start) + 1
        json_end = response_text.find("```", json_start)
        if json_end > json_start:
          response_text = response_text[json_start:json_end].strip()

      response_data = json.loads(response_text)

      # Check if this is a Claude CLI wrapper response
      if isinstance(response_data, dict) and "result" in response_data and isinstance(response_data["result"], str):
        # Extract the content from the result field
        result_content = response_data["result"]

        # Try to find JSON in various formats
        json_content = None

        # Check if the result contains markdown-wrapped JSON
        if "```json" in result_content and "```" in result_content:
          # Extract JSON from markdown code block
          json_start = result_content.find("```json") + 7
          json_start = result_content.find("\n", json_start) + 1
          json_end = result_content.find("```", json_start)
          if json_end > json_start:
            json_content = result_content[json_start:json_end].strip()

        # If no markdown block found, try to find raw JSON
        if not json_content:
          # Look for JSON starting with { and ending with }
          json_start = result_content.find("{")
          if json_start >= 0:
            # Find the matching closing brace
            brace_count = 0
            json_end = json_start
            for i in range(json_start, len(result_content)):
              if result_content[i] == "{":
                brace_count += 1
              elif result_content[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                  json_end = i + 1
                  break
            if json_end > json_start:
              json_content = result_content[json_start:json_end]

        if json_content:
          actual_result = json.loads(json_content)
          response_data = actual_result
          logger.debug("Extracted JSON from Claude CLI wrapper")
        else:
          raise ValueError("Could not find valid JSON in response")

      # Debug logging
      if self.verbose:
        logger.debug(f"Parsed response type: {type(response_data)}")
        if isinstance(response_data, dict):
          logger.debug(f"Response keys: {list(response_data.keys())[:5]}...")

      # Cache the response
      with open(cache_file, "w") as f:
        json.dump(response_data, f, indent=2)

      return response_data

    except subprocess.CalledProcessError as e:
      logger.error(f"Claude CLI error: {e}")
      logger.error(f"stderr: {e.stderr}")
      raise
    except json.JSONDecodeError as e:
      logger.error(f"Failed to parse Claude response as JSON: {e}")
      logger.error(f"Response: {result.stdout[:500]}...")
      # Try to save the raw response for debugging
      debug_file = self.cache_dir / f"debug_{cache_key}.txt"
      with open(debug_file, "w") as f:
        f.write(result.stdout)
      logger.error(f"Full response saved to: {debug_file}")
      raise

  def update_provider(self, provider_name: str) -> dict[str, Any]:
    """Update models for a specific provider"""
    if provider_name not in PROVIDERS:
      raise ValueError(f"Unknown provider: {provider_name}")

    provider = PROVIDERS[provider_name]
    logger.info(f"Updating {provider_name} models...")

    # Get search prompt from provider module
    search_prompt = provider.get_search_prompt()

    # Query Claude for model information
    try:
      model_data = self.query_claude(search_prompt)
    except Exception as e:
      logger.error(f"Failed to query Claude for {provider_name}: {e}")
      return {}

    # Validate and format the data
    try:
      validated_data = provider.validate_and_format(model_data)
      logger.info(f"Retrieved {len(validated_data)} models for {provider_name}")
      return validated_data
    except Exception as e:
      logger.error(f"Failed to validate {provider_name} data: {e}")
      return {}

  def load_models_json(self) -> dict[str, Any]:
    """Load existing Models.json"""
    if MODELS_JSON_PATH.exists():
      try:
        with open(MODELS_JSON_PATH) as f:
          return json.load(f)
      except Exception as e:
        logger.error(f"Error reading Models.json: {e}")
        return {}
    else:
      logger.warning("Models.json not found, will create new file")
      return {}

  def save_models_json(self, models_data: dict[str, Any]):
    """Save updated Models.json"""
    # Create backup
    if MODELS_JSON_PATH.exists():
      backup_path = MODELS_JSON_PATH.with_suffix(".json.backup")
      try:
        with open(MODELS_JSON_PATH) as f_in, open(backup_path, "w") as f_out:
          f_out.write(f_in.read())
        logger.info(f"Created backup at {backup_path}")
      except Exception as e:
        logger.warning(f"Could not create backup: {e}")

    # Save updated data
    with open(MODELS_JSON_PATH, "w") as f:
      json.dump(models_data, f, indent=2)
    logger.info(f"Updated Models.json with {len(models_data)} models")

  def merge_model_data(self, existing: dict[str, Any], new_models: dict[str, Any]) -> dict[str, Any]:
    """Merge new model data with existing, preserving user settings"""
    from datetime import datetime

    merged = existing.copy()
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build alias lookup table from existing models
    alias_lookup = {}
    for model_id, model in existing.items():
      if "alias" in model and model["alias"]:
        alias_lookup[model["alias"]] = model_id

    for model_id, model_data in new_models.items():
      # Check for alias conflicts
      if "alias" in model_data and model_data["alias"]:
        proposed_alias = model_data["alias"]

        # Check if this alias is already used by a different model
        if proposed_alias in alias_lookup and alias_lookup[proposed_alias] != model_id:
          conflict_model = alias_lookup[proposed_alias]
          logger.warning(f"Alias conflict: '{proposed_alias}' already used by {conflict_model}")

          # Create a new alias by prefixing with model name
          model_prefix = model_id.replace(" ", "").replace("-", "")
          new_alias = f"{model_prefix}-{proposed_alias}"
          logger.warning(f"Changing alias for {model_id} from '{proposed_alias}' to '{new_alias}'")
          model_data["alias"] = new_alias

          # Update alias lookup with the new alias
          alias_lookup[new_alias] = model_id
        else:
          # No conflict, add to lookup
          alias_lookup[proposed_alias] = model_id

      # Check if model is new or has changed
      is_new = model_id not in existing
      has_changed = False

      if not is_new:
        # Compare key fields to detect changes
        existing_model = existing[model_id]
        check_fields = ["context_window", "max_output_tokens", "token_costs", "data_cutoff_date", "description", "vision", "model_category"]

        for field in check_fields:
          if field in model_data and field in existing_model and model_data[field] != existing_model[field]:
            has_changed = True
            logger.debug(f"Model {model_id} field '{field}' changed: {existing_model[field]} -> {model_data[field]}")
            break

      # Add or update info_updated timestamp
      if is_new or has_changed:
        model_data["info_updated"] = current_timestamp
        if is_new:
          logger.info(f"New model added: {model_id}")
        else:
          logger.info(f"Model updated: {model_id}")
      elif model_id in existing and "info_updated" in existing[model_id]:
        # Preserve existing info_updated timestamp
        model_data["info_updated"] = existing[model_id]["info_updated"]

      # Preserve user settings for existing models
      if model_id in existing:
        model_data["enabled"] = existing[model_id].get("enabled", model_data.get("enabled", 0))
        model_data["available"] = existing[model_id].get("available", model_data.get("available", 1))

        # Preserve any other custom fields that might exist
        for key in existing[model_id]:
          if key not in model_data and key not in ["info_updated"]:
            model_data[key] = existing[model_id][key]

      merged[model_id] = model_data

    return merged

  def show_diff(self, existing: dict[str, Any], updated: dict[str, Any]):
    """Show differences between existing and updated data"""
    added = set(updated.keys()) - set(existing.keys())
    removed = set(existing.keys()) - set(updated.keys())
    modified = []

    for model_id in set(existing.keys()) & set(updated.keys()):
      if existing[model_id] != updated[model_id]:
        modified.append(model_id)

    if added:
      logger.info(f"New models to add: {len(added)}")
      for model_id in sorted(added)[:5]:
        logger.info(f"  + {model_id}")
      if len(added) > 5:
        logger.info(f"  ... and {len(added) - 5} more")

    if removed:
      logger.info(f"Models to remove: {len(removed)}")
      for model_id in sorted(removed)[:5]:
        logger.info(f"  - {model_id}")

    if modified:
      logger.info(f"Models to update: {len(modified)}")
      for model_id in sorted(modified)[:5]:
        logger.info(f"  * {model_id}")
      if len(modified) > 5:
        logger.info(f"  ... and {len(modified) - 5} more")

  def update_all_providers(self) -> dict[str, Any]:
    """Update models for all providers"""
    all_models = {}

    for provider_name in PROVIDERS:
      provider_models = self.update_provider(provider_name)
      all_models.update(provider_models)

    return all_models

  def run(self, providers: list[str] = None, update_all: bool = False):
    """Main execution method"""
    # Load existing models
    existing_models = self.load_models_json()

    # Get new model data
    if update_all:
      new_models = self.update_all_providers()
    else:
      new_models = {}
      for provider in providers or []:
        provider_models = self.update_provider(provider)
        new_models.update(provider_models)

    # Merge with existing data
    updated_models = self.merge_model_data(existing_models, new_models)

    # Show differences
    self.show_diff(existing_models, updated_models)

    # Save or show dry run
    if self.dry_run:
      logger.info("Dry run mode - no changes made")
    else:
      self.save_models_json(updated_models)


def main():
  """Main entry point"""
  # Get program name without .py extension
  prog_name = os.path.basename(sys.argv[0])
  if prog_name.endswith(".py"):
    prog_name = prog_name[:-3]

  # Create dynamic epilog with usage examples
  epilog = f"""
Usage Examples:
  {prog_name} --all                 # Update all providers
  {prog_name} --provider anthropic  # Update specific provider
  {prog_name} --all --dry-run       # Preview changes
  {prog_name} --list-providers      # List available providers
    """

  parser = argparse.ArgumentParser(
    prog=prog_name,
    description="Update Models.json using Claude CLI web searches",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=epilog,
  )

  # Provider selection
  parser.add_argument(
    "--provider", "-p", action="append", choices=list(PROVIDERS.keys()), help="Provider to update (can be specified multiple times)"
  )
  parser.add_argument("--all", "-a", action="store_true", help="Update all providers")
  parser.add_argument("--list-providers", "-l", action="store_true", help="List available providers and exit")

  # Options
  parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without modifying Models.json")
  parser.add_argument("--force", "-f", action="store_true", help="Force update, bypassing cache")
  parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
  parser.add_argument(
    "--model",
    "-m",
    default="sonnet",
    choices=["sonnet", "opus", "none"],
    help='Claude model to use for searches (default: sonnet). Use "none" to omit --model parameter',
  )

  args = parser.parse_args()

  # Handle list providers
  if args.list_providers:
    print("Available providers:")
    for provider in sorted(PROVIDERS.keys()):
      print(f"  - {provider}")
    return

  # Validate arguments
  if not args.all and not args.provider:
    parser.error("Please specify --all or at least one --provider")

  # Set up logging level
  if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)

  # Create updater instance
  updater = ClaudeModelUpdater(dry_run=args.dry_run, verbose=args.verbose, force=args.force, model=args.model)

  # Run updates
  try:
    updater.run(providers=args.provider, update_all=args.all)
  except Exception as e:
    logger.error(f"Update failed: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()

# fin
