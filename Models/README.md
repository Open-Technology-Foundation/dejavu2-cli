# DejaVu2-CLI Models Registry

This directory contains the model registry and tools for the DejaVu2-CLI application.

## Models.json

The `Models.json` file serves as the central registry for all available AI models in the DejaVu2-CLI application. It defines the models, their capabilities, and configuration parameters used when making API calls to various providers.

### Structure

Each model entry in the JSON file contains the following fields:

- **model**: The canonical model identifier used in API calls to providers
- **alias**: A short nickname for easy reference in CLI commands
- **parent**: The provider organization (Anthropic, OpenAI, Google, Meta, etc.)
- **model_category**: Type of model functionality:
  - `LLM`: Text generation models
  - `image`: Image generation models (e.g., DALL-E)
  - `tts`: Text-to-speech models
  - `stt`: Speech-to-text models
  - `embed`: Embedding/vector models
  - `audio`: Audio processing models
  - `moderation`: Content moderation models
- **family**: Model family grouping (e.g., claude3, gpt4, llama3)
- **series**: Sub-grouping within a family
- **description**: Human-readable explanation of the model's capabilities
- **training_data**: Date/period when the model was trained (informational)
- **data_cutoff_date**: Knowledge cutoff date for the model (informational)
- **url**: Primary API endpoint for making requests
- **url2**: Fallback API endpoint (optional)
- **apikey**: Environment variable name containing the required API credentials
- **context_window**: Maximum input token limit
- **max_output_tokens**: Maximum response length limit
- **token_costs**: Cost information (informational only)
- **vision**: Flag indicating vision capabilities (1=yes)
- **available**: Availability flag (0=unavailable, values > 0=available)
- **enabled**: Control flag (0=disabled, values > 0=enabled)
- **output_dimension**: Vector dimensions for embedding models

### Usage in Code

The Models.json registry is used throughout the DejaVu2-CLI application:

1. **Model Selection**:
   - Models are loaded from Models.json into memory
   - User model requests are matched by name or alias
   - Availability and enabled status are verified

2. **API Parameter Configuration**:
   - Provider-specific parameters are extracted
   - Context window and token limits are enforced
   - API URLs and authentication are configured

3. **Request Routing**:
   - The `parent` field determines which provider client to use
   - Model-specific parameters are applied to API calls

4. **Filtering and Display**:
   - Models can be filtered by various attributes
   - Different display formats are available (default, short, long)

### Flags and Levels

The `available` and `enabled` fields use a numeric level system:

- **available**:
  - `0`: Model is not available
  - `1-9`: Model is available, with higher numbers indicating higher availability
  
- **enabled**:
  - `0`: Model is disabled and cannot be used
  - `1-9`: Model is enabled, with higher numbers indicating preferred models

These numeric levels allow for filtering models by availability or enabled status, such as showing only models with availability level <= 5.

## Utilities

### dv2-list-models

The `dv2-list-models` script provides a command-line interface for browsing and filtering models defined in Models.json.

Usage examples:

```bash
# Show all models in default format
./dv2-list-models

# Show all models with full details
./dv2-list-models -m long

# Show only OpenAI models
./dv2-list-models -p openai

# Show enabled GPT-4 family models
./dv2-list-models -f gpt4 -e 1

# Show enabled OpenAI LLM models in detail
./dv2-list-models -m long -p openai -c llm -e 1

# Show models with alias 'sonnet'
./dv2-list-models -a sonnet

# Show all available models for level 9 (highest) and lower
./dv2-list-models -v 9
```

### Model Information Scripts

#### get-anthropic-models.sh

This script retrieves and displays information about the latest Anthropic models. It shows details such as:

- Model display name and ID
- Creation date
- Context window size
- Maximum output tokens
- Token costs
- Data cutoff date
- Vision capability
- Suggested alias

The script also provides a JSON format example for each model that can be used to update Models.json.

Usage:
```bash
./get-anthropic-models.sh
```

#### get-openai-models.sh

This script displays information about the latest OpenAI models. It covers a wide range of models including:

- o1 and o1-mini
- GPT-4o and GPT-4o Mini
- ChatGPT-4o
- Specialized models (DALL-E 3, TTS, Whisper)
- Embedding models

For each model, it provides:
- Model category and family
- Context window and output limits
- Token costs
- Detailed descriptions
- JSON format examples for updating Models.json

Usage:
```bash
./get-openai-models.sh
```

#### update_anthropic_models.py

This Python script dynamically fetches and updates only Anthropic model information in Models.json. It:

1. Downloads the latest Anthropic model data from their API documentation
2. Caches the HTML content in .cache/anthropic/ for future use
3. Updates Models.json with current Anthropic models, including:
   - Context window sizes
   - Maximum output token limits
   - Token costs
   - Data cutoff dates
   - Vision capabilities
4. Automatically handles both versioned models and "latest" models
5. For new models, sets 'available' to 1 and 'enabled' to 0
6. Preserves existing enabled/available states for models already in Models.json
7. Creates a backup of the original file before making changes

Usage:
```bash
# Update Models.json with Anthropic models
./update_anthropic_models.py

# Dry run (show what would be changed without modifying the file)
./update_anthropic_models.py --dry-run

# Skip downloading new content and use cached versions
./update_anthropic_models.py --skip-download
```

#### update_openai_models.py

This Python script updates OpenAI model information in Models.json. It:

1. Uses the OpenAI API to get a list of all available models
2. Combines this with hardcoded pricing and capability information
3. Updates Models.json with current OpenAI models, including:
   - Context window sizes
   - Maximum output token limits
   - Token costs
   - Data cutoff dates
   - Vision capabilities
4. Identifies and prioritizes "latest" model versions
5. For new models, sets 'available' to 1 and 'enabled' to 0
6. Preserves existing enabled/available states for models already in Models.json
7. Creates a backup of the original file before making changes

Usage:
```bash
# First fetch model data from OpenAI API
./examine_openai_models.py

# Update Models.json with OpenAI models
./update_openai_models.py

# Dry run (show what would be changed without modifying the file)
./update_openai_models.py --dry-run
```

These scripts require Python packages, which can be installed in a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests openai
```

### Adding New Models Manually

When adding new models to the registry:

1. Add a new JSON object with all required fields
2. Follow the naming convention of existing models
3. Set appropriate `available` and `enabled` flags
4. Ensure the `parent` field matches one of the supported providers
5. Specify the correct environment variable in `apikey`
6. Set reasonable values for `context_window` and `max_output_tokens`

Example:
```json
"new-model-name": {
  "model": "new-model-name",
  "alias": "newmodel",
  "parent": "Provider",
  "model_category": "LLM",
  "family": "model-family",
  "series": "model-series",
  "description": "Description of the new model",
  "training_data": "2024-03",
  "data_cutoff_date": "2024-03",
  "url": "https://api.provider.com/v1",
  "apikey": "PROVIDER_API_KEY",
  "context_window": 100000,
  "max_output_tokens": 4096,
  "token_costs": "$X.XX per 1K tokens",
  "vision": 0,
  "available": 9,
  "enabled": 1
}
```