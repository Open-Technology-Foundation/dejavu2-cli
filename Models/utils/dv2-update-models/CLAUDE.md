# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands
- Update all providers: `./claude-update-models.py --all` or `./dv2-models-update --all`
- Update specific provider: `./claude-update-models.py --provider anthropic`
- Update multiple providers: `./claude-update-models.py --provider anthropic --provider openai`
- Preview changes: `./claude-update-models.py --all --dry-run`
- Force update (bypass cache): `./claude-update-models.py --all --force`
- List providers: `./claude-update-models.py --list-providers`
- Verbose mode: `./claude-update-models.py --provider openai --verbose`
- Model selection: `./claude-update-models.py --provider anthropic --model opus`

## Code Standards
- Python: Shebang `#!/usr/bin/env python3`
- Scripts must be executable (chmod +x)
- Scripts must end with `#fin` on last line
- Imports: stdlib → third-party → local, alphabetically sorted
- Type hints: Use typing module (Dict, List, Any, Optional)
- Logging: Use logging module, not print()
- JSON: 2-space indentation
- Cache files stored in XDG_CACHE_HOME or ~/.cache/dv2-models-update

## Architecture Overview
- **Main Script**: `claude-update-models.py` - Uses claude CLI to query model information
- **ClaudeModelUpdater**: Core class handling queries, caching, merging, and updates
- **Provider Modules**: `providers/` directory contains provider-specific logic
  - Each provider implements `get_search_prompt()` and `validate_and_format()`
  - BaseProvider abstract class defines interface
- **Models.json**: Located at `../../Models.json` (3 levels up from script)
- **Cache System**: 24-hour cache in ~/.cache/dv2-models-update/ with model-specific keys
- **Symlink**: `dv2-models-update` → `claude-update-models.py`

## Provider Module Structure
Each provider module must:
1. Inherit from BaseProvider
2. Implement `get_search_prompt()` - Returns prompt for Claude to search provider docs
3. Implement `validate_and_format()` - Validates and formats Claude's response
4. Export module-level functions for compatibility

Currently implemented:
- `anthropic.py` - Full implementation with current model loading
- `openai.py` - Full implementation (check parent directory for reference)

Stub providers (TODO):
- `google.py`, `mistral.py`, `cohere.py`, `ollama.py`

## Key Features
- **Smart Caching**: Cache key includes model selection (sonnet/opus/none)
- **Change Tracking**: Adds `info_updated` timestamp when models are new/changed
- **Alias Conflict Resolution**: Automatically resolves duplicate aliases
- **User Setting Preservation**: Preserves `enabled` and `available` values
- **Backup System**: Creates .backup file before updating Models.json
- **JSON Extraction**: Handles various Claude response formats (markdown, wrapped, raw)

## Critical Path: Query → Process → Merge → Save
1. Provider generates search prompt (may include current models)
2. Claude queries web for latest model information
3. Response parsed from various JSON formats
4. Provider validates and formats data
5. Merge preserves user settings, detects changes
6. Alias conflicts resolved automatically
7. Backup created, Models.json updated

## Development Guidelines
- Test with `--dry-run` before making changes
- Use `--verbose` to debug Claude responses
- Check cache files in ~/.cache/dv2-models-update/ for debugging
- Failed JSON parsing saves raw response to debug_*.txt
- Always preserve existing user settings (`enabled`, `available`)
- New models default to `available=1, enabled=0`

## Adding New Providers
1. Create `providers/newprovider.py`
2. Implement BaseProvider interface
3. Add to PROVIDERS dict in main script
4. Test with dry-run mode first
5. Ensure JSON response validation is robust

## Common Issues
- **JSON Parsing**: Claude may wrap JSON in markdown or include explanatory text
- **Cache Keys**: Include model parameter to avoid cache conflicts
- **Alias Conflicts**: System auto-resolves by prefixing with model name
- **Missing Fields**: Provider modules should set sensible defaults

#fin