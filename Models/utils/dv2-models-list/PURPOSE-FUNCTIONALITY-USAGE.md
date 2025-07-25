# PURPOSE-FUNCTIONALITY-USAGE

## Project Overview

**dejavu2-cli** (dv2) is a powerful command-line interface for interacting with multiple Large Language Models (LLMs) from various providers including OpenAI, Anthropic, Google, and local models via Ollama. It serves as a unified interface for AI-powered conversations with persistent context management and extensive customization options.

The **dv2-models-list** utility is a specialized tool within the Models directory that provides advanced querying and management capabilities for the AI model registry used by dejavu2-cli.

## Purpose

### dejavu2-cli
- **Primary Goal**: Provide a seamless, unified CLI for accessing multiple LLM providers
- **Target Users**: Developers, researchers, and power users who need command-line access to AI models
- **Key Problems Solved**:
  - Eliminates need for multiple provider-specific tools
  - Maintains conversation context across sessions
  - Simplifies model switching and parameter tuning
  - Enables integration with knowledge bases and reference files

### dv2-models-list
- **Primary Goal**: Advanced model registry management and querying
- **Key Problems Solved**:
  - Filter and search models across multiple providers
  - Generate statistics and insights about available models
  - Export model data in various formats (JSON, CSV, YAML, table)
  - Validate model configurations

## Core Functionality

### dejavu2-cli Main Features

1. **Multi-Provider Support**
   - OpenAI (GPT-4, GPT-3.5, O1/O3 models)
   - Anthropic (Claude 3 family)
   - Google (Gemini models)
   - Local models via Ollama server
   - Custom endpoints for self-hosted models

2. **Conversation Management**
   - Persistent conversation history stored in JSON
   - Continue previous conversations with context
   - Export conversations to markdown format
   - Manage message history (view, remove messages)
   - Automatic conversation titling

3. **Template System (Agents)**
   - Pre-configured parameter sets for common tasks
   - Categories: General, Specialist, Edit-Summarize, etc.
   - Includes specialized agents like biographers, advisors, coders

4. **Context Enhancement**
   - Include reference files in queries
   - Integration with customKB knowledge bases
   - Maintain system prompts across conversations

5. **Model Management**
   - Over 100 pre-configured models
   - Alias system for quick model selection
   - Automatic parameter adjustment per model type
   - Update scripts for provider catalogs

### dv2-models-list Features

1. **Advanced Filtering**
   - Filter by any model field (parent, alias, enabled, etc.)
   - Complex queries with AND/OR logic
   - Numeric comparisons (>=, <=, !=)
   - String matching (contains, starts_with, regex)

2. **Multiple Output Formats**
   - Table view with customizable columns
   - JSON export for programmatic use
   - CSV for spreadsheet analysis
   - YAML for configuration files
   - Tree view grouped by provider/family

3. **Statistics & Analysis**
   - Model count by provider
   - Token cost analysis
   - Availability distribution
   - Context window comparisons

## Common Usage Patterns

### Basic dejavu2-cli Usage

```bash
# Simple query with default model (sonnet)
dv2 "Explain quantum computing"

# Use specific model by alias
dv2 "Write a poem about nature" -m gpt4o

# Continue last conversation
dv2 "Tell me more about that" -c

# Use a template for specialized tasks
dv2 "Analyze this Python code" -T "Coder - Code Expert" -r script.py

# Export conversation
dv2 -e current -f quantum_discussion.md
```

### Conversation Workflows

```bash
# Start new conversation with title
dv2 "Let's discuss machine learning" --title "ML Discussion"

# List all conversations
dv2 --list-conversations

# Continue specific conversation
dv2 "What about neural networks?" -C 550e8400-e29b-41d4-a716

# View conversation status
dv2 --conversation 550e8400-e29b-41d4-a716 --status
```

### Model Discovery with dv2-models-list

```bash
# Find all Claude models
./dv2-models-list -F "parent:equals:Anthropic"

# Find enabled GPT-4 models
./dv2-models-list -F "family:equals:gpt4" -F "enabled:>=:1"

# Show only vision-capable models
./dv2-models-list -F "vision:equals:1" --format table --columns model,alias,parent

# Export all OpenAI models to JSON
./dv2-models-list -F "parent:equals:OpenAI" --format json > openai_models.json

# Get statistics by provider
./dv2-models-list --count-by parent
```

## Architecture Overview

### dejavu2-cli Structure
- **Entry Points**: `dv2` (bash wrapper) → `main.py` (Python CLI)
- **Core Modules**:
  - `llm_clients.py`: Provider API integrations
  - `conversations.py`: Conversation persistence
  - `models.py`: Model registry interface
  - `templates.py`: Agent/template management
  - `config.py`: Configuration handling
  - `security.py`: Input validation
- **Data Storage**:
  - Conversations: `~/.config/dejavu2-cli/conversations/`
  - Configuration: `defaults.yaml`, `Models.json`, `Agents.json`

### dv2-models-list Structure
- **Main Script**: `dv2-models-list.py`
- **Filter System**: Modular filter classes for flexible queries
- **Formatters**: Pluggable output format handlers
- **Statistics**: Analytics module for model insights

## Key Dependencies

- **Python 3.7+** (3.8+ recommended)
- **API Libraries**: openai, anthropic, google.generativeai
- **CLI Framework**: Click
- **Configuration**: PyYAML
- **Testing**: pytest, pytest-cov

## Important Notes

1. **API Keys Required**: Set environment variables for providers you want to use:
   - `ANTHROPIC_API_KEY`
   - `OPENAI_API_KEY`
   - `GOOGLE_API_KEY`

2. **Model Availability**: Models have availability levels (0-9) that determine if they can be used

3. **Security**: All inputs are validated, API keys never logged, secure subprocess handling

4. **Performance**: Lazy loading of clients, conversation caching, efficient model filtering

5. **Extensibility**: Modular design allows easy addition of new providers, models, and features

This toolkit provides a comprehensive solution for command-line AI interactions with enterprise-grade features for conversation management, model selection, and integration capabilities.

#fin