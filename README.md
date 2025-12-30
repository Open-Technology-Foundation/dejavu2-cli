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

**Current Version**: 0.9.1

## Features

### Core Capabilities
- **Multi-Provider Support**: OpenAI (GPT-4/5, O1/O3/O4), Anthropic (Claude 3.5/4), Google (Gemini 2.0/2.5), Ollama
- **Unified Interface**: Single CLI for all LLM providers with consistent parameter handling
- **Conversation Management**: Persistent history with file locking for concurrent access safety
- **Agent Templates**: 28 pre-configured AI personas with specialized capabilities
- **Context Enhancement**: Include reference files and knowledgebases in queries
- **Security-First Design**: Input validation, secure subprocess execution, SDK-specific exception handling

### Advanced Features
- **Model Registry**: 69 models (39 enabled) with aliases and metadata across all providers
- **Smart Parameter Handling**: Automatic adjustment for model-specific requirements (O-series reasoning, Gemini configs)
- **Multiple Output Formats**: Export conversations to markdown, view in various formats
- **Robust Error Handling**: SDK-specific exceptions with graceful degradation
- **Extensible Architecture**: Modular design for easy feature additions

## Installation

### Prerequisites

- Python 3.12 or higher
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
dv2 "Debug this Python code: print(1/0)" -T leet

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
├── models.py            # Model registry and selection
├── templates.py         # Agent template management
├── context.py           # Reference files and knowledgebases
├── config.py            # Configuration loading and management
├── security.py          # Input validation and secure execution
├── errors.py            # Custom exception hierarchy
├── display.py           # Output formatting and status display
├── utils.py             # Utility functions
└── version.py           # Version information
```

### Key Components

#### LLM Clients (`llm_clients.py`)
Handles API interactions with different providers:
- **OpenAI**: GPT-4/5 and O-series (O1/O3/O4) with Responses API and reasoning effort config
- **Anthropic**: Claude 3.5/4 models with beta headers for extended thinking
- **Google**: Gemini 2.0/2.5 via `google-genai` SDK with subprocess isolation for GRPC
- **Ollama**: Local and remote server support with robust response parsing

#### Conversation Management (`conversations.py`)
Persistent conversation storage with:
- JSON-based storage in `~/.config/dejavu2-cli/conversations/`
- File locking (`fcntl.flock`) for concurrent access safety
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
| `-V, --version` | Show version and exit |
| `-m, --model MODEL` | Select model by name or alias (e.g., `gpt4o`, `sonnet`) |
| `-T, --template NAME` | Use an agent template (e.g., `leet`, `dejavu2`) |
| `-t, --temperature FLOAT` | Set creativity level (0.0-1.0) |
| `-M, --max-tokens INT` | Maximum response length |
| `-s, --systemprompt TEXT` | Custom system instructions |

### Conversation Management

| Option | Description |
|--------|-------------|
| `-c, --continue` | Continue the most recent conversation |
| `-C, --conversation ID` | Continue a specific conversation |
| `-n, --new-conversation` | Force start a new conversation |
| `-i, --title TEXT` | Set a title for a new conversation |
| `-x, --list-conversations` | List all saved conversations |
| `-X, --delete-conversation ID` | Delete a specific conversation |
| `-e, --export-conversation ID` | Export conversation to markdown (ID or "current") |
| `-f, --export-path PATH` | Path to save exported markdown file |
| `-O, --stdout` | Output exported conversation to stdout |
| `-W, --list-messages ID` | Show all messages in a conversation |
| `--remove-message ID INDEX` | Remove a specific message |
| `--remove-pair ID INDEX` | Remove a user-assistant message pair |
| `-g, --message ROLE TEXT` | Add message pairs (e.g., `-g user "hello"`) |

### Context and References

| Option | Description |
|--------|-------------|
| `-r, --reference FILES` | Include reference files (comma-separated) |
| `-k, --knowledgebase NAME` | Use a knowledgebase for context |
| `-Q, --knowledgebase-query` | Custom query for knowledgebase |

### Information and Configuration

| Option | Description |
|--------|-------------|
| `-S, --status` | Display current configuration |
| `-P, --print-systemprompt` | Print full system prompt with --status |
| `-a, --list-models` | List available models |
| `-A, --list-models-details` | List models with all details |
| `-l, --list-template NAME` | Show template details ("all" for all) |
| `-L, --list-template-names` | List template names without systemprompts |
| `-K, --list-knowledge-bases` | List available knowledgebases |
| `-E, --edit-templates` | Edit Agents.json |
| `-D, --edit-defaults` | Edit defaults.yaml |
| `-d, --edit-models` | Edit Models.json |

### Output and Logging

| Option | Description |
|--------|-------------|
| `-p, --project-name NAME` | Project name for recording conversations |
| `-o, --output-dir DIR` | Directory to output results |
| `-v, --verbose` | Enable verbose (debug level) logging |
| `--log-file PATH` | Path to log file |
| `-q, --quiet` | Suppress log messages except errors |

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
"claude-sonnet-4-5-20250514": {
  "model": "claude-sonnet-4-5-20250514",
  "alias": "sonnet",
  "parent": "Anthropic",
  "family": "anthropic",
  "model_category": "LLM",
  "context_window": 200000,
  "max_output_tokens": 64000,
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
1. **Full model ID**: `claude-sonnet-4-5-20250514`
2. **Alias**: `sonnet`
3. **Partial match**: `gpt4` (matches `gpt-4o`)

## Agents Module

The Agents module provides 28 pre-configured AI personas with specialized capabilities.

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
  "model": "sonnet",
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
  --model claude-sonnet-4-5-20250514 --temperature 0.7

# Edit existing agent
./Agents/dv2-agents edit "Leet"
```

### Using Agents

Agents are selected via the `-T` option:
```bash
# Use the Leet programmer for code review
dv2 "Review this Python function for security issues" -T leet -r code.py

# Use the Legal specialist
dv2 "Explain this contract clause" -T legal

# Use the Editor for improving text
dv2 "Improve this paragraph" -T editor
```

**Note**: When specifying an agent with `-T|--template`, only the agent key is required (case-insensitive). To list agent keys: `jq -r 'keys[]' Agents.json | cut -d' ' -f1`

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
   - 69 model definitions
   - Provider configurations

4. **Agents.json** - Agent templates
   - 28 pre-configured AI personas
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
dv2 "Summarize these reports" -r report1.pdf,report2.docx -T summary

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
# Note: when specifying an agent with the -T|--template option, only the
# Agent key is required. It is non-case sensitive.
# To get a list of Agent template keys:  jq -r 'keys[]' Agents.json | cut -d' ' -f1

# Use the Dejavu2 general assistant
dv2 "Help me understand this concept" -T dejavu2

# Use specialized agents for domain tasks
dv2 "Get business advice for Indonesia" -T askokusi
dv2 "Find bugs in this code" -T leet -r app.js
dv2 "Diagnose these symptoms" -T diffdiagnosis

# Content processing agents
dv2 "Improve this text" -T subeditor -r draft.txt
dv2 "Summarize this report" -T summariser -r report.pdf
dv2 "Convert to markdown" -T text2md -r document.txt

# Creative and specialized agents
dv2 "Create a short video idea" -T vazz
dv2 "Interview me about my life" -T bio
dv2 "Write a children's story" -T charlesdodgson
dv2 "Create a Twitter post" -T x_post

# Other useful agents
dv2 "Get factual answers" -T virgo
dv2 "Translate this text" -T trans -r document.txt
dv2 "Ask with humor" -T sarki

# Combine agents with specific parameters
dv2 "Debug this Python code" -T leet -m opus -t 0.2 -r buggy_code.py
```

### Knowledgebase Integration

The `customkb` integration allows you to query vector databases for enhanced context:

```bash
# Basic knowledgebase query
dv2 "What is our coding standard?" -k "engineering_docs"

# Specify custom query for the knowledgebase
dv2 "Explain the deployment process" -k "devops_kb" -Q "kubernetes deployment procedures"

# Combine knowledgebase with agent templates
dv2 "Review this code against our standards" -T leet -k "coding_standards" -r new_feature.py

# Multiple context sources
dv2 "Is this compliant with our policies?" -k "company_policies" -r proposal.pdf
```

**Available Knowledgebases**:
- List all available knowledgebases: `dv2 -K`
- Knowledgebases are stored in `/var/lib/vectordbs/`
- Each KB has a configuration file defining its content and indexing

### Advanced Usage
```bash
# Chain commands with context
dv2 "Analyze this data" -r data.csv | dv2 "Create a summary report" -c

# Complex multi-context query
dv2 "Review architecture" -T devops -k "best_practices" -r architecture.md -m opus

# Export formatted conversation
dv2 "Let's design a system" -T architect -c | dv2 -e current -O > design_discussion.md
```

## Development

### Project Structure
```
dejavu2-cli/
├── Core Modules
│   ├── main.py              # CLI orchestration
│   ├── llm_clients.py       # Provider integrations
│   ├── conversations.py     # History management
│   ├── models.py            # Model selection
│   ├── templates.py         # Agent management
│   ├── context.py           # Reference handling
│   ├── config.py            # Configuration
│   ├── security.py          # Security layer
│   ├── errors.py            # Exception hierarchy
│   ├── display.py           # Output formatting
│   ├── utils.py             # Utility functions
│   └── version.py           # Version information
├── Configuration
│   ├── defaults.yaml        # System defaults
│   ├── Models.json          # Model registry (symlink)
│   └── Agents.json          # Agent templates (symlink)
├── Submodules
│   ├── Models/              # Model management tools
│   │   ├── Models.json      # Model registry
│   │   ├── dv2-models-list  # Model listing tool
│   │   └── dv2-models-update # Model update tool
│   └── Agents/              # Agent management tools
│       ├── Agents.json      # Agent templates
│       └── dv2-agents       # Agent management tool
├── Utils
│   └── bash_completions/    # Shell completion scripts
└── Tests
    ├── unit/                # Unit tests
    ├── integration/         # Integration tests
    └── functional/          # End-to-end tests
```

### Coding Standards
- **Python Style**: 2-space indentation, 100 char line limit
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Documentation**: Google-style docstrings for all public APIs
- **Error Handling**: Use custom exceptions from `errors.py`
- **File Endings**: All Python scripts must end with `#fin`

### Testing

The test suite includes 325 tests across unit, integration, and functional categories.

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
   - Add client initialization to `initialize_clients()` in `llm_clients.py`
   - Add query function (e.g., `query_provider()`) with SDK-specific exception handling
   - Update `route_query_by_family()` to route to new provider
   - Add models to `Models.json` with appropriate family/parent fields
   - Add tests for new provider in `tests/unit/test_llm_clients.py`

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

**Current Version**: 0.9.1 | **Status**: Active Development | **Python**: 3.12+

#fin
