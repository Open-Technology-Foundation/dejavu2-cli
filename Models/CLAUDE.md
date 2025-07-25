# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands
- Update Anthropic models: `python update_anthropic_models.py` or `./update_anthropic_models`
- Update OpenAI models: `python update_openai_models.py` or `./update_openai_models`
- List models: `python dv2-list-models.py [options]` or `./dv2-list-models [options]`
- Check Models.json integrity: `python check_models_json.py`

## Code Standards
- Python: Shebang `#!/usr/bin/env python3`
- Scripts must be executable (chmod +x)
- JSON files use 2-space indentation
- All scripts should handle errors gracefully with proper logging
- Update scripts create backups before modifying Models.json

## Architecture Overview
- **Models.json**: Central registry for all AI models across providers
- **Update Scripts**: 
  - `update_anthropic_models.py` - Updates Anthropic models using web scraping and cached data
  - `update_openai_models.py` - Updates OpenAI models from API and hardcoded pricing data
- **Query Tools**:
  - `dv2-list-models.py` - Lists and filters models with various display modes
  - `check_models_json.py` - Validates Models.json structure and checks for duplicates
- **Caching**: Update scripts use `.cache/` directory to store provider data

## Models.json Structure
Key fields for each model entry:
- `model`: Official model identifier for API calls
- `alias`: Short nickname for CLI usage
- `parent`: Provider organization (OpenAI, Anthropic, Google, etc.)
- `model_category`: Type (LLM, image, embed, tts, stt, moderation)
- `context_window`: Maximum input tokens
- `max_output_tokens`: Maximum response length
- `available`: 0-9 availability level (0=unavailable, 9=production)
- `enabled`: 0-9 enabled status (0=disabled, 9=preferred)
- `vision`: 1=supports vision, 0=text only

## Development Notes
- Update scripts support `--dry-run` mode to preview changes
- Models with `available=0` or `enabled=0` are filtered out by default
- New models start with `available=1, enabled=0` for testing
- Always preserve existing model settings when updating
- Use numeric levels (0-9) for fine-grained availability/preference control

#fin