# WAH.ID Model Registry

This directory contains the model registry and configuration tools for the WAH.ID platform, allowing integration with multiple LLM providers.

## Models.json Structure

The `Models.json` file serves as the central registry for all AI models available in the WAH.ID platform. It defines models, their capabilities, and configuration parameters used when connecting to various LLM providers.

### Field Definitions

Each model entry in the `Models.json` file contains the following fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `model` | String | Official model identifier used in API calls | `"gpt-4o"` |
| `alias` | String | Short nickname for easy reference in commands | `"g4o"` |
| `parent` | String | Provider organization | `"OpenAI"`, `"Anthropic"`, `"Google"` |
| `model_category` | String | Type of model functionality | `"LLM"`, `"image"`, `"embed"` |
| `family` | String | Model family grouping | `"gpt4"`, `"claude3"`, `"gemini"` |
| `series` | String | Sub-grouping within a family | `"opus"`, `"sonnet"`, `"haiku"` |
| `description` | String | Human-readable explanation of capabilities | `"Latest flagship model with..."` |
| `training_data` | String | Date/period when trained | `"2023-12"` |
| `data_cutoff_date` | String | Knowledge cutoff date (YYYY-MM-DD) | `"2023-12-01"` |
| `url` | String | Primary API endpoint | `"https://api.openai.com/v1"` |
| `url2` | String | Fallback API endpoint (optional) | `"https://api-fallback.openai.com/v1"` |
| `apikey` | String | Environment variable name for API credentials | `"OPENAI_API_KEY"` |
| `context_window` | Number | Maximum input token limit | `128000` |
| `max_output_tokens` | Number | Maximum response length limit | `4096` |
| `token_costs` | String | Cost information (informational only) | `"$0.01/0.03 per 1K tokens"` |
| `vision` | Number | Vision capabilities flag (1=yes, 0=no) | `1` |
| `available` | Number | Availability level (0-9) | `9` |
| `enabled` | Number | Control flag (0=disabled, 1-9=enabled) | `1` |
| `output_dimension` | Number | Vector dimensions for embedding models | `1536` |

### Model Categories

The `model_category` field classifies models by their primary function:

- `LLM`: Text generation models (e.g., GPT-4, Claude 3)
- `image`: Image generation models (e.g., DALL-E 3, Midjourney)
- `tts`: Text-to-speech models (e.g., OpenAI TTS)
- `stt`: Speech-to-text models (e.g., Whisper)
- `embed`: Embedding/vector models (e.g., text-embedding-3-large)
- `audio`: Audio processing models
- `moderation`: Content moderation models

### Availability and Enabled Flags

The numeric level system for `available` and `enabled` fields allows fine-grained control:

#### Available Flag
- `0`: Model is not available (API down, deprecated, etc.)
- `1-3`: Low availability (limited capacity, experimental)
- `4-6`: Medium availability (generally reliable)
- `7-9`: High availability (production-ready)

#### Enabled Flag
- `0`: Model is disabled and cannot be used
- `1-3`: Enabled for testing or limited use
- `4-6`: Enabled for general use
- `7-9`: Preferred models (highlighted in UI)

These numeric levels allow filtering models by availability level or preference tier.

### Example Model Entry

```json
"claude-3-7-sonnet-20250219": {
  "model": "claude-3-7-sonnet-20250219",
  "alias": "c3.7s",
  "parent": "Anthropic",
  "model_category": "LLM",
  "family": "claude3",
  "series": "sonnet",
  "description": "Claude 3.7 Sonnet - balanced LLM with enhanced reasoning",
  "training_data": "2025-02",
  "data_cutoff_date": "2025-02-01",
  "url": "https://api.anthropic.com/v1/messages",
  "apikey": "ANTHROPIC_API_KEY",
  "context_window": 200000,
  "max_output_tokens": 4096,
  "token_costs": "$0.013/0.015 per 1K tokens",
  "vision": 1,
  "available": 9,
  "enabled": 9
}
```

## Integration with WAH.ID

### Model Selection Flow

1. **Initialization**:
   - The `llm_query.php` system loads models from `Models.json` on startup
   - Models are filtered by `available` and `enabled` status
   - Default models are selected based on priority settings

2. **User Selection**:
   - Users select models through the Control Panel interface
   - Model selection is stored in the user's state via `StateManagerV3`
   - The selection persists across sessions until changed

3. **API Request Process**:
   - When a query is made, the system uses the model configuration to:
     - Format the message appropriately for the provider
     - Set context window constraints
     - Apply token limits
     - Select the correct endpoint URL
     - Use the appropriate environment variable for authentication

### Provider-Specific Processing

Each provider requires specific message formatting and parameter handling:

- **OpenAI**: JSON with roles, content objects, and vision handlers
- **Anthropic**: Messages with human/assistant structure and media objects
- **Google**: Structured content format with parts and inline data
- **Ollama**: Local model handling with specific parameter mapping
- **Azure**: OpenAI-compatible with custom authentication mechanism
- **Custom/Local**: Configuration for custom endpoints and models

## Managing Models

### Adding New Models

To add a new model:

1. Create a new JSON object entry in `Models.json`
2. Ensure all required fields are populated
3. Set appropriate `available` and `enabled` flags (typically start with `available: 1, enabled: 0`)
4. Verify the `parent` field matches a supported provider
5. Specify the correct environment variable in `apikey`
6. Use accurate values for `context_window` and `max_output_tokens`

### Updating Model Information

Use the provided utilities to keep model information current:

- `get-anthropic-models.sh`: Retrieves the latest Anthropic model specifications
- `get-openai-models.sh`: Shows updated OpenAI model information
- `update_anthropic_models.py`: Automatically updates Anthropic models in the registry
- `update_openai_models.py`: Automatically updates OpenAI models in the registry

Before making changes, the update scripts create backups and can be run in dry-run mode to preview changes.

In WAHID website, Models can be managed at //modelman.php

### Listing Available Models

Use the `dv2-list-models` utility to view and filter models:

```bash
# Show all enabled models
./dv2-list-models -e 1

# Show only Anthropic models with detailed information
./dv2-list-models -p anthropic -m long

# Show models with vision capabilities
./dv2-list-models --vision
```

## Security Considerations

- API keys are never stored in `Models.json`, only environment variable names
- Enable only the models you need to minimize risk and cost
- Set appropriate availability levels based on reliability testing
- Monitor usage patterns to detect anomalies
- Keep model information updated to maintain security and performance

#fin