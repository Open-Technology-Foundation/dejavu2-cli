# AI Model Registry

This directory maintains the canonical `Models.json` file - a comprehensive registry of AI models that serves as the central source of truth for multiple applications and utilities.

## Overview

The `Models.json` file is a critical infrastructure component that provides:
- Unified model definitions across multiple AI providers (OpenAI, Anthropic, Google, Meta, xAI, etc.)
- Standardized configuration parameters for consistent API interactions
- Model capabilities, limitations, and availability status
- Cost information and usage constraints

### Applications Using Models.json

This registry powers several applications:
- **dejavu2-cli / dv2**: Command-line LLM interface with multi-provider support
- **customkb**: Knowledge base system with AI integration
- **WAHID website**: Web-based AI interaction platform
- **Various utility programs**: Model selection, cost analysis, and capability checking tools

## Models.json Structure

Each model entry contains standardized fields that enable consistent handling across applications:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `model` | String | Official API identifier | `"gpt-4o"`, `"claude-3-5-sonnet-latest"` |
| `alias` | String | Short memorable nickname | `"g4o"`, `"sonnet35"` |
| `parent` | String | Provider organization | `"OpenAI"`, `"Anthropic"`, `"Google"` |
| `model_category` | String | Functional type | `"LLM"`, `"image"`, `"embed"`, `"tts"` |
| `family` | String | Model lineage group | `"gpt4"`, `"claude3"`, `"gemini"` |
| `series` | String | Sub-family classification | `"opus"`, `"sonnet"`, `"haiku"` |
| `description` | String | Human-readable capabilities | `"Advanced reasoning model with..."` |
| `training_data` | String | Training period | `"2024-10"` |
| `data_cutoff_date` | String | Knowledge cutoff (YYYY-MM-DD) | `"2024-10-01"` |
| `url` | String | Primary API endpoint | `"https://api.openai.com/v1"` |
| `url2` | String | Fallback endpoint (optional) | `"https://api-fallback.openai.com/v1"` |
| `apikey` | String | Environment variable name | `"OPENAI_API_KEY"` |
| `context_window` | Number | Maximum input tokens | `128000` |
| `max_output_tokens` | Number | Maximum response tokens | `4096` |
| `token_costs` | String | Pricing information | `"$5.00/$15.00 per 1M tokens"` |
| `vision` | Number | Vision capability (0/1) | `1` |
| `available` | Number | Availability level (0-9) | `9` |
| `enabled` | Number | Enabled status (0-9) | `1` |
| `output_dimension` | Number | Embedding vector size | `1536` |
| `info_updated` | String | Last update timestamp | `"2025-07-25 11:50:42"` |

### Availability and Enabled Levels

**Available** (0-9): Provider-side availability
- `0`: Not available (deprecated, API down)
- `1-3`: Limited availability (experimental, beta)
- `4-6`: Generally available
- `7-9`: Production-ready, high availability

**Enabled** (0-9): Local usage preference
- `0`: Disabled (won't be used)
- `1-3`: Testing/development use
- `4-6`: General use
- `7-9`: Preferred models

## Utility Scripts

### dv2-models-list
Advanced model query and analysis tool with powerful filtering capabilities.

```bash
# List all enabled models
dv2-models-list

# Filter by provider
dv2-models-list -p OpenAI

# Show in table format with vision models only
dv2-models-list -o table --vision

# Complex filtering
dv2-models-list -F "context_window:>=:100000" -F "parent:equals:Anthropic"

# Export to different formats
dv2-models-list -o json > models.json
dv2-models-list -o csv > models.csv

# Show statistics
dv2-models-list -S
```

**Features**:
- Multiple output formats (table, json, csv, yaml, tree)
- Advanced filtering with operators (equals, contains, >, <, between, regex)
- Statistical analysis mode
- Sorting and limiting options
- Filter presets for common queries

### dv2-models-update
Intelligent update system using Claude CLI to fetch latest model information.

```bash
# Update all providers
dv2-models-update --all

# Update specific providers
dv2-models-update --provider anthropic --provider openai

# Preview changes without applying
dv2-models-update --all --dry-run

# Use different Claude model for searches
dv2-models-update --all --model opus

# Force update (bypass cache)
dv2-models-update --provider google --force
```

**Features**:
- Real-time web searches for current model info
- Automatic conflict resolution for aliases
- Change tracking with timestamps
- 24-hour intelligent caching
- Backup creation before updates
- Dry-run mode for safety

### check_models_json.py
Validates the integrity of Models.json file.

```bash
# Run validation
python check_models_json.py
```

**Validations**:
- JSON syntax correctness
- Duplicate model IDs
- Duplicate aliases
- Required fields presence
- Data type validation
- Provider distribution report

## Best Practices

### For Application Developers
1. **Never modify Models.json directly** - Use update scripts to maintain consistency
2. **Check both `available` and `enabled`** - Models need both to be usable
3. **Use aliases for user-facing interfaces** - They're more memorable than model IDs
4. **Handle missing optional fields** - Not all models have all fields
5. **Cache model data appropriately** - The registry can be large

### For Model Registry Maintainers
1. **Run validation after manual edits**: `python check_models_json.py`
2. **Use dry-run first**: Test updates with `--dry-run` before applying
3. **Keep backups**: The update script creates them automatically
4. **Update regularly**: Model information changes frequently
5. **Preserve custom settings**: Update scripts maintain local modifications

### Adding New Models
1. Use the update scripts when possible - they ensure consistency
2. For manual additions, include all required fields
3. Start new models with `available: 1, enabled: 0` for testing
4. Ensure aliases are unique across all models
5. Validate the file after changes

## Security Considerations

- **API Keys**: Never stored in Models.json - only environment variable names
- **Endpoints**: Verify URLs are legitimate provider endpoints
- **Access Control**: Limit write access to Models.json
- **Validation**: Always validate after updates to prevent injection
- **Backups**: Maintain backups before any modifications

## Directory Structure

```
Models/
├── Models.json              # The canonical model registry
├── README.md               # This documentation
├── CLAUDE.md               # Claude Code guidance
├── check_models_json.py    # Validation utility
├── dv2-models-list         # Symlink to query utility
├── dv2-models-update       # Symlink to update utility
└── utils/
    ├── dv2-models-list/    # Model query and analysis tool
    │   ├── dv2-models-list.py
    │   ├── filters/        # Filter implementations
    │   ├── formatters/     # Output formatters
    │   └── ...
    └── dv2-update-models/  # Claude-based update system
        ├── claude-update-models.py
        ├── providers/      # Provider-specific modules
        └── ...
```

## Quick Reference

```bash
# List available models
dv2-models-list

# Update model information
dv2-models-update --all

# Validate registry
python check_models_json.py

# Find specific models
dv2-models-list -F "model:contains:gpt"

# Export for analysis
dv2-models-list -o csv > analysis.csv

# Check provider coverage
dv2-models-list -S
```

## Troubleshooting

**Models not appearing in applications:**
- Check `enabled` > 0
- Verify `available` > 0
- Ensure required fields are present
- Validate JSON syntax

**Update script failures:**
- Check internet connectivity
- Verify Claude CLI is installed and configured
- Clear cache if getting stale results: `rm -rf .cache/`
- Use `--force` to bypass cache

**Validation errors:**
- Run `check_models_json.py` for detailed error report
- Check for duplicate aliases
- Ensure numeric fields contain numbers, not strings

#fin