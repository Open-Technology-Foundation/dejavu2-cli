# dejavu2-cli

A powerful command-line interface for interacting with various Large Language Models (LLMs) including OpenAI, Anthropic Claude, Google Gemini, and local models via Ollama.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Command-Line Interface](#command-line-interface)
- [Models Module](#models-module)
- [Agents Module](#agents-module)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

`dejavu2-cli` (also available as `dv2`) is a versatile command-line tool for executing queries to multiple language models from various providers. It provides a unified interface for AI interactions with support for conversation history, contextual inputs, customizable parameters, and agent templates.

**Current Version**: 0.8.30

## Features

### Core Capabilities
- **Multi-Provider Support**: Seamlessly interact with models from OpenAI, Anthropic, Google, Meta, xAI, and local Ollama instances
- **Unified Interface**: Single CLI for all LLM providers with consistent parameter handling
- **Conversation Management**: Maintain context across sessions with persistent conversation history
- **Agent Templates**: Pre-configured AI personas with specialized capabilities
- **Context Enhancement**: Include reference files and knowledge bases in queries
- **Security-First Design**: Built-in input validation and secure subprocess execution

### Advanced Features
- **Model Registry**: Comprehensive database of 100+ models with aliases and metadata
- **Smart Parameter Handling**: Automatic adjustment for model-specific requirements (e.g., O1/O3 models)
- **Multiple Output Formats**: Export conversations to markdown, view in various formats
- **Robust Error Handling**: Graceful degradation with meaningful error messages
- **Extensible Architecture**: Modular design for easy feature additions

## Installation

### Prerequisites

- Python 3.7 or higher (3.8+ recommended)
- pip package manager
- Git (for cloning the repository)
- API keys for desired LLM providers

### Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Open-Technology-Foundation/dejavu2-cli.git
   cd dejavu2-cli
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up API Keys**
   ```bash
   # For Anthropic models (Claude)
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
   
   # For OpenAI models (GPT, O1, O3)
   export OPENAI_API_KEY="your_openai_api_key"
   
   # For Google models (Gemini)
   export GOOGLE_API_KEY="your_google_api_key"
   
   # Ollama models work without API key (local server)
   ```

4. **Verify Installation**
   ```bash
   ./dv2 --version
   ```

## Quick Start

```bash
# Basic query using default model (Claude Sonnet)
dv2 "Explain quantum computing in simple terms"

# Use a specific model by alias
dv2 "Write a haiku about coding" -m gpt4o

# Use an agent template for specialized tasks
dv2 "Debug this Python code: print(1/0)" -T "Leet - Full-Stack Programmer"

# Continue a conversation
dv2 "What are its practical applications?" -c

# Include reference files
dv2 "Summarize this document" -r report.pdf,data.csv
```

## Architecture

### Module Overview

The codebase follows a modular architecture with clear separation of concerns:

```
Core Modules:
├── main.py              # CLI entry point and orchestration
├── llm_clients.py       # LLM provider API integrations
├── conversations.py     # Conversation history management
├── models.py           # Model registry and selection
├── templates.py        # Agent template management
├── context.py          # Reference files and knowledge bases
├── config.py           # Configuration loading and management
├── security.py         # Input validation and secure execution
├── errors.py           # Custom exception hierarchy
├── display.py          # Output formatting and status display
├── utils.py            # Utility functions
└── version.py          # Version information
```

### Key Components

#### LLM Clients (`llm_clients.py`)
Handles API interactions with different providers:
- **OpenAI**: Standard and O1/O3 model support with parameter adjustments
- **Anthropic**: Claude models with native API integration
- **Google**: Gemini models via generativeai library
- **Ollama**: Local and remote server support with robust response parsing

#### Conversation Management (`conversations.py`)
Persistent conversation storage with:
- JSON-based storage in `~/.config/dejavu2-cli/conversations/`
- Message history with metadata tracking
- Export capabilities to markdown format
- Message manipulation (removal, pair deletion)

#### Security Layer (`security.py`)
Comprehensive security features:
- Input validation for queries and file paths
- Secure subprocess execution with whitelisting
- Command injection prevention
- Configurable security policies

## Command-Line Interface

### Basic Usage
```bash
dv2 [QUERY] [OPTIONS]
```

### Primary Options

| Option | Description |
|--------|-------------|
| `-m, --model MODEL` | Select model by name or alias (e.g., `gpt4o`, `sonnet`) |
| `-T, --template NAME` | Use an agent template (e.g., `"Coder - Software Expert"`) |
| `-t, --temperature FLOAT` | Set creativity level (0.0-1.0) |
| `-M, --max-tokens INT` | Maximum response length |
| `-s, --systemprompt TEXT` | Custom system instructions |

### Conversation Management

| Option | Description |
|--------|-------------|
| `-c, --continue` | Continue the most recent conversation |
| `-C, --conversation ID` | Continue a specific conversation |
| `-n, --new-conversation` | Force start a new conversation |
| `-x, --list-conversations` | List all saved conversations |
| `-e, --export-conversation ID` | Export conversation to markdown |
| `-W, --list-messages ID` | Show all messages in a conversation |
| `--remove-message ID INDEX` | Remove a specific message |
| `--remove-pair ID INDEX` | Remove a user-assistant message pair |

### Context and References

| Option | Description |
|--------|-------------|
| `-r, --reference FILES` | Include reference files (comma-separated) |
| `-k, --knowledgebase NAME` | Use a knowledge base for context |
| `-Q, --knowledgebase-query` | Custom query for knowledge base |

### Information and Configuration

| Option | Description |
|--------|-------------|
| `-S, --status` | Display current configuration |
| `-a, --list-models` | List available models |
| `-l, --list-template NAME` | Show template details |
| `-K, --list-knowledge-bases` | List available knowledge bases |
| `-E, --edit-templates` | Edit Agents.json |
| `-D, --edit-defaults` | Edit defaults.yaml |

## Models Module

The Models module maintains a comprehensive registry of AI models across all supported providers.

### Model Registry (`Models.json`)

Each model entry contains:
- **Identification**: model ID, alias, provider, family
- **Capabilities**: context window, max tokens, vision support
- **Availability**: enabled/available status (0-9 scale)
- **Metadata**: descriptions, training dates, pricing

Example model entry:
```json
"claude-3-7-sonnet-latest": {
  "model": "claude-3-7-sonnet-latest",
  "alias": "sonnet",
  "parent": "Anthropic",
  "model_category": "LLM",
  "context_window": 200000,
  "max_output_tokens": 128000,
  "vision": 1,
  "available": 9,
  "enabled": 1
}
```

### Model Management Tools

#### List Models (`dv2-models-list`)
Advanced querying and filtering:
```bash
# List all enabled models
./Models/dv2-models-list

# Filter by provider
./Models/dv2-models-list -F "parent:equals:OpenAI"

# Complex queries
./Models/dv2-models-list -F "context_window:>:100000" -F "vision:equals:1"

# Export formats
./Models/dv2-models-list -o json
./Models/dv2-models-list -o table -col model,alias,context_window
```

#### Update Models (`dv2-models-update`)
Claude-powered intelligent updates:
```bash
# Update all providers
./Models/dv2-models-update --all

# Update specific provider
./Models/dv2-models-update --provider anthropic

# Dry run mode
./Models/dv2-models-update --all --dry-run
```

### Model Selection
Models can be selected by:
1. **Full model ID**: `claude-3-7-sonnet-latest`
2. **Alias**: `sonnet`
3. **Partial match**: `gpt4` (matches `gpt-4o`)

## Agents Module

The Agents module provides pre-configured AI personas with specialized capabilities.

### Agent Registry (`Agents.json`)

Agents are organized by category:
- **General**: Multi-purpose assistants
- **Specialist**: Domain experts (coding, legal, medical, etc.)
- **Edit-Summarize**: Content processing specialists

### Agent Configuration

Each agent defines:
```json
"Leet - Full-Stack Programmer": {
  "category": "Specialist",
  "systemprompt": "You are Leet, an expert full-stack programmer...",
  "model": "claude-3-7-sonnet-latest",
  "max_tokens": 8000,
  "temperature": 0.35,
  "monospace": true,
  "available": 9,
  "enabled": 9
}
```

### Agent Management

#### Command-Line Tool (`dv2-agents`)
```bash
# List all agents
./Agents/dv2-agents list

# View specific agent
./Agents/dv2-agents list "Leet"

# List by category
./Agents/dv2-agents list -c Specialist

# Create new agent
./Agents/dv2-agents insert "NewAgent - Description" \
  --model claude-3-7-sonnet-latest --temperature 0.7

# Edit existing agent
./Agents/dv2-agents edit "Leet"
```

### Using Agents

Agents are selected via the `-T` option:
```bash
# Use the Leet programmer for code review
dv2 "Review this Python function for security issues" -T "Leet" -r code.py

# Use the Legal specialist
dv2 "Explain this contract clause" -T "Legal - Law and Regulations"

# Use the Editor for improving text
dv2 "Improve this paragraph" -T "Editor - Text Improvement"
```

## Configuration

### Configuration Files

1. **defaults.yaml** - System defaults
   ```yaml
   defaults:
     template: Dejavu2
     model: sonnet
     temperature: 0.1
     max_tokens: 4000
   
   security:
     subprocess:
       timeout: 30.0
       allowed_editors: ["nano", "vim", "vi", "emacs", "joe"]
   ```

2. **User Configuration** - `~/.config/dejavu2-cli/config.yaml`
   - Overrides system defaults
   - User-specific settings

3. **Models.json** - Model registry
   - Comprehensive model database
   - Provider configurations

4. **Agents.json** - Agent templates
   - Pre-configured AI personas
   - Specialized system prompts

### Configuration Hierarchy
1. Command-line arguments (highest priority)
2. Agent template settings
3. User configuration
4. System defaults (lowest priority)

## Usage Examples

### Basic Interactions
```bash
# Simple question
dv2 "What is the capital of France?"

# Creative writing with high temperature
dv2 "Write a short story about AI" -t 0.9

# Technical analysis with low temperature
dv2 "Explain TCP/IP networking" -m opus -t 0.1
```

### Working with Files
```bash
# Analyze code
dv2 "Review this code for bugs" -r main.py,utils.py

# Summarize documents
dv2 "Summarize these reports" -r report1.pdf,report2.docx -T "Summary"

# Compare files
dv2 "What are the differences between these configs?" -r old.yaml,new.yaml
```

### Conversation Management
```bash
# Start a titled conversation
dv2 "Let's discuss machine learning" --title "ML Discussion"

# Continue conversation
dv2 "What about neural networks?" -c

# Export conversation
dv2 -e current -f ml_discussion.md

# Review conversation history
dv2 -x
dv2 -W 550e8400-e29b-41d4-a716-446655440000
```

### Using Agent Templates
```bash
# Use the Dejavu2 general assistant
dv2 "Help me understand this concept" -T Dejavu2

# Use specialized agents for domain tasks
dv2 "Get business advice for Indonesia" -T askOkusi
dv2 "Find bugs in this code" -T Leet -r app.js
dv2 "Diagnose these symptoms" -T DiffDiagnosis

# Content processing agents
dv2 "Improve this text" -T SubEditor -r draft.txt
dv2 "Summarize this report" -T Summariser -r report.pdf
dv2 "Convert to markdown" -T Text2md -r document.txt

# Creative and specialized agents
dv2 "Create a short video idea" -T Vazz
dv2 "Interview me about my life" -T Bio
dv2 "Write a children's story" -T CharlesDodgson
dv2 "Create a Twitter post" -T X_Post

# Other useful agents
dv2 "Get factual answers" -T Virgo
dv2 "Translate this text" -T TRANS -r document.txt
dv2 "Ask with humor" -T Sarki

# Combine agents with specific parameters
dv2 "Debug this Python code" -T Leet -m opus -t 0.2 -r buggy_code.py
```

### Knowledge Base Integration

The `customkb` integration allows you to query vector databases for enhanced context:

```bash
# Basic knowledge base query
dv2 "What is our coding standard?" -k "engineering_docs"

# Specify custom query for the knowledge base
dv2 "Explain the deployment process" -k "devops_kb" -Q "kubernetes deployment procedures"

# Combine knowledge base with agent templates
dv2 "Review this code against our standards" -T "Leet" -k "coding_standards" -r new_feature.py

# Multiple context sources
dv2 "Is this compliant with our policies?" -k "company_policies" -r proposal.pdf
```

**Available Knowledge Bases**:
- List all available knowledge bases: `dv2 -K`
- Knowledge bases are stored in `/var/lib/vectordbs/`
- Each KB has a configuration file defining its content and indexing

### Advanced Usage
```bash
# Chain commands with context
dv2 "Analyze this data" -r data.csv | dv2 "Create a summary report" -c

# Complex multi-context query
dv2 "Review architecture" -T "DevOps" -k "best_practices" -r architecture.md -m opus

# Export formatted conversation
dv2 "Let's design a system" -T "Architect" -c | dv2 -e current -O > design_discussion.md
```

## Development

### Project Structure
```
dejavu2-cli/
├── Core Modules
│   ├── main.py              # CLI orchestration
│   ├── llm_clients.py       # Provider integrations
│   ├── conversations.py     # History management
│   ├── models.py           # Model selection
│   ├── templates.py        # Agent management
│   ├── context.py          # Reference handling
│   ├── config.py           # Configuration
│   ├── security.py         # Security layer
│   ├── errors.py           # Exception hierarchy
│   └── display.py          # Output formatting
├── Configuration
│   ├── defaults.yaml       # System defaults
│   ├── Models.json        # Model registry
│   └── Agents.json        # Agent templates
├── Submodules
│   ├── Models/            # Model management tools
│   └── Agents/            # Agent management tools
└── Tests
    ├── unit/              # Unit tests
    ├── integration/       # Integration tests
    └── functional/        # End-to-end tests
```

### Coding Standards
- **Python Style**: 2-space indentation, 100 char line limit
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Documentation**: Google-style docstrings for all public APIs
- **Error Handling**: Use custom exceptions from `errors.py`
- **File Endings**: All Python scripts must end with `#fin`

### Testing
```bash
# Run all tests
./run_tests.sh

# Run specific test categories
./run_tests.sh --unit
./run_tests.sh --integration
./run_tests.sh --functional

# Run with coverage
./run_tests.sh --coverage

# Run specific test
python -m pytest tests/unit/test_security.py -v
```

### Adding New Features

1. **New LLM Provider**
   - Add client class to `llm_clients.py`
   - Update `initialize_clients()` and `query()` functions
   - Add models to `Models.json`
   - Create provider update module in `Models/utils/dv2-update-models/providers/`

2. **New Agent Template**
   - Add entry to `Agents.json`
   - Use `dv2-agents insert` command
   - Test with various queries
   - Set appropriate availability/enabled levels

3. **New CLI Option**
   - Add Click option to `main.py`
   - Update relevant processing functions
   - Add tests for new functionality
   - Update documentation

## Troubleshooting

### Common Issues

**API Key Problems**
```bash
# Check if keys are set
dv2 --status | grep "API Keys"

# Verify specific key
echo $ANTHROPIC_API_KEY
```

**Model Not Found**
```bash
# List available models
dv2 --list-models

# Check model details
./Models/dv2-models-list -F "alias:contains:sonnet"
```

**Conversation Issues**
```bash
# List conversations
dv2 -x

# Clean up old conversations
dv2 -X [conversation-id]

# Force new conversation
dv2 "query" -n
```

**Ollama Connection**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Use remote Ollama server
export OLLAMA_HOST=https://your-server.com
```

### Debug Mode
```bash
# Enable verbose logging
dv2 "test query" -v

# Log to file
dv2 "test query" --log-file debug.log

# Check configuration
dv2 --status -P
```

## License

This project is licensed under the GPL-3.0 License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please:
1. Review [CLAUDE.md](CLAUDE.md) for development guidelines
2. Follow the coding standards
3. Add tests for new features
4. Update documentation as needed

## Support

- **Issues**: [GitHub Issues](https://github.com/Open-Technology-Foundation/dejavu2-cli/issues)
- **Documentation**: Check `docs/` directory for detailed guides
- **Community**: Join discussions in the issues section

---

**Current Version**: 0.8.30 | **Status**: Active Development | **Python**: 3.7+

#fin