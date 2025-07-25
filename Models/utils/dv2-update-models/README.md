# Claude-based Models.json Update System

A robust system that uses the `claude` CLI tool with `--print` flag to perform comprehensive web searches and update Models.json with the latest LLM model information from major providers.

## Overview

This system replaces the fragile, hardcoded update scripts with an intelligent solution that:
- Uses Claude to search for current model information in real-time
- Adapts to documentation changes automatically
- Supports multiple AI providers
- Provides caching, validation, and rollback capabilities

## Features

- **Real-time Updates**: Claude performs web searches to find the latest model information
- **Multi-provider Support**: Anthropic, OpenAI, Google, Mistral, Cohere, Ollama
- **Smart Caching**: 24-hour cache to avoid redundant searches (cache keys include model selection)
- **Model Selection**: Choose between sonnet (default), opus, or none for Claude searches
- **Validation**: Ensures data consistency and format compliance
- **Change Tracking**: Automatically adds `info_updated` timestamp when models are new or changed
- **Alias Conflict Resolution**: Detects and resolves duplicate aliases automatically
- **Backup System**: Automatic backups before updates
- **Dry Run Mode**: Preview changes without modifying files
- **Extensible**: Easy to add new providers

## Installation

The system is already installed in the Models directory. Ensure you have:
- `claude` CLI tool installed and configured
- Python 3.7+ 
- Required Python packages from the main requirements.txt

## Usage

### Update All Providers
```bash
./claude-update-models.py --all
```

### Update Specific Provider
```bash
./claude-update-models.py --provider anthropic
./claude-update-models.py --provider openai
```

### Multiple Providers
```bash
./claude-update-models.py --provider anthropic --provider openai
```

### Dry Run (Preview Changes)
```bash
./claude-update-models.py --all --dry-run
```

### Force Update (Bypass Cache)
```bash
./claude-update-models.py --all --force
```

### List Available Providers
```bash
./claude-update-models.py --list-providers
```

### Verbose Output
```bash
./claude-update-models.py --provider openai --verbose
```

### Model Selection
```bash
# Use default model (sonnet)
./claude-update-models.py --provider anthropic

# Use opus model (more powerful but slower)
./claude-update-models.py --provider anthropic --model opus

# Use no model parameter (uses Claude's default)
./claude-update-models.py --provider anthropic --model none
```

## How It Works

1. **Provider Selection**: Choose which providers to update
2. **Claude Query**: The system sends a detailed prompt to Claude asking for:
   - Official documentation links
   - Current model lists
   - Specifications (context windows, output limits)
   - Pricing information
   - Capabilities (vision, multimodal, etc.)
   - Data cutoff dates
3. **Response Processing**: Claude returns structured JSON data
4. **Validation**: Provider modules validate and format the data
5. **Merge**: New data is merged with existing Models.json, preserving user settings
6. **Backup & Save**: Creates backup and saves updated file

## Provider Modules

Each provider has a dedicated module in `providers/`:

### Implemented Providers
- **anthropic.py**: Full support for Claude models
- **openai.py**: Full support for GPT, O1/O3, DALL-E, Whisper, etc.

### Stub Providers (TODO)
- **google.py**: Gemini models
- **mistral.py**: Mistral and Mixtral models  
- **cohere.py**: Command and Embed models
- **ollama.py**: Local models via Ollama

## Cache Management

- Responses are cached for 24 hours in `.cache/`
- Cache files are named by prompt hash
- Use `--force` to bypass cache
- Cache automatically expires after 24 hours

## Error Handling

- Network errors: Falls back to cached data if available
- Invalid responses: Logs errors and skips problematic models
- Validation failures: Reports issues without corrupting Models.json

## Automatic Features

### Change Tracking
- Each model gets an `info_updated` timestamp when:
  - It's newly added to Models.json
  - Any key field changes (context window, pricing, output tokens, etc.)
- Existing timestamps are preserved if no changes detected

### Alias Conflict Resolution
- System checks all aliases to prevent duplicates
- If a conflict is detected:
  - Logs a warning about the conflict
  - Creates a new alias: `{modelname}-{originalalias}`
  - Example: If "sonnet" is taken, "claude-3-5-sonnet-latest" becomes "claude35sonnetlatest-sonnet"

## Extending the System

To add a new provider:

1. Create `providers/newprovider.py`:
```python
from . import BaseProvider

class NewProvider(BaseProvider):
    @staticmethod
    def get_search_prompt() -> str:
        return "Search prompt for Claude..."
    
    @staticmethod
    def validate_and_format(raw_data):
        # Validation logic
        return formatted_models

get_search_prompt = NewProvider.get_search_prompt
validate_and_format = NewProvider.validate_and_format
```

2. Import in main script:
```python
from providers import newprovider
PROVIDERS['newprovider'] = newprovider
```

## Advantages Over Previous System

1. **Always Current**: Real-time searches ensure up-to-date information
2. **No Hardcoding**: No model data to manually maintain
3. **Adaptable**: Claude understands context and adapts to doc changes
4. **Comprehensive**: Searches multiple sources for complete data
5. **Reliable**: Validation and error handling prevent corruption

## Troubleshooting

### Claude CLI Not Found
Ensure `claude` is installed and in your PATH:
```bash
which claude
```

### Empty Responses
- Check Claude API availability
- Verify prompts are clear and specific
- Look for rate limiting issues

### Validation Errors
- Check provider module implementation
- Enable verbose mode for detailed logs
- Manually inspect Claude's response in cache

## Future Enhancements

- [ ] Implement remaining provider modules
- [ ] Add changelog generation
- [ ] Create visual diff tool
- [ ] Add scheduling for automatic updates
- [ ] Implement rollback functionality
- [ ] Add model comparison features

#fin