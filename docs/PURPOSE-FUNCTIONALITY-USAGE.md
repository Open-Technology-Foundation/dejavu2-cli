# Dejavu2-CLI: Purpose, Functionality, and Usage

## Executive Summary

**Dejavu2-cli** is a sophisticated command-line interface that provides unified access to multiple Large Language Models (LLMs) including OpenAI (GPT-4, O1/O3), Anthropic Claude, Google Gemini, and local/remote Ollama models. It solves the fragmentation problem in the LLM ecosystem by offering a single, consistent interface with advanced features like conversation persistence, context integration, and template management.

## Purpose

### Problem Solved
The LLM landscape is fragmented across multiple providers, each with distinct APIs, authentication methods, and interfaces. Users must juggle different tools, learn multiple syntaxes, and handle provider-specific quirks. Dejavu2-cli eliminates this complexity by providing a unified interface to all major LLMs.

### Target Audience
- **Software Developers**: Integrating AI into applications and workflows
- **Data Scientists/Researchers**: Comparing model responses and conducting AI research
- **System Administrators**: Automating tasks with LLM capabilities
- **Technical Writers**: Leveraging AI for documentation and content
- **AI Enthusiasts**: Experimenting with different models and features

## Key Functionality

### 1. Multi-Provider LLM Support
- **OpenAI**: GPT-4, GPT-3.5, O1/O3 models with specialized parameter handling
- **Anthropic**: Claude-3.5-Sonnet and other Claude variants
- **Google**: Gemini models via Google Generative AI
- **Ollama**: Local and remote open-source models (LLaMA, Mistral, etc.)

### 2. Conversation Management
- **Persistent History**: Conversations saved as JSON files with complete context
- **Session Continuity**: Resume conversations across sessions with `-c` flag
- **Export Capabilities**: Generate Markdown exports of conversations
- **Message Management**: View, remove, and manage individual messages

### 3. Context Enhancement
- **Reference Files**: Include multiple files as context (`-r file1.txt,file2.txt`)
- **Knowledge Bases**: Integrate with customKB vector databases (`-k knowledge_base`)
- **Dynamic Assembly**: Automatically formats and includes context in queries

### 4. Template System
- **Predefined Templates**: Stored in `Agents.json` for common use cases
- **Parameter Presets**: Consistent model, temperature, and prompt configurations
- **Easy Management**: List, view, and edit templates from CLI

### 5. Advanced Features
- **Model Aliases**: Use shortcuts like "sonnet" instead of full model names
- **Security Validation**: Input sanitization and secure subprocess handling
- **Comprehensive Logging**: Debug, info, and error logging with file output
- **Configuration Hierarchy**: System defaults → user config → CLI overrides

## Common Usage Patterns

### Basic Query
```bash
# Simple one-off query
dv2 "What is the capital of France?"

# Using model alias
dv2 "Explain quantum computing" -m sonnet
```

### Using Templates
```bash
# Use a predefined template
dv2 "Summarize this article" -T "Summariser - Summary Machine"

# List available templates
dv2 -L
```

### Context Integration
```bash
# Include reference files
dv2 "Review this code for issues" -r main.py,utils.py

# Query with knowledge base
dv2 "What are the latest findings?" -k research_papers
```

### Conversation Management
```bash
# Start a new conversation with title
dv2 "Let's discuss AI ethics" --title "AI Ethics Discussion"

# Continue the last conversation
dv2 "What about privacy concerns?" -c

# Continue specific conversation
dv2 "Tell me more" -C 550e8400-e29b-41d4-a716

# Export conversation
dv2 -e current -f ~/Documents/ai_ethics.md
```

### Advanced Operations
```bash
# List all models with details
dv2 -A

# Edit templates
dv2 -E

# Check current configuration
dv2 --status -P

# Batch processing
for file in *.txt; do
    dv2 "Summarize this" -r "$file" >> summaries.md
done
```

## Installation & Setup

### Prerequisites
- Python 3.7+ with pip
- API keys for desired providers (as environment variables)
- Optional: Ollama server for local models

### Quick Start
```bash
# Clone repository
git clone https://github.com/Open-Technology-Foundation/dejavu2-cli.git
cd dejavu2-cli

# Install dependencies
pip install -r requirements.txt

# Set API keys
export ANTHROPIC_API_KEY="your_key"
export OPENAI_API_KEY="your_key"
export GOOGLE_API_KEY="your_key"

# Run first query
./dv2 "Hello, AI!"
```

## Architecture Overview

### Modular Design
- **main.py**: CLI orchestration with Click framework
- **llm_clients.py**: Provider-specific API clients
- **conversations.py**: Conversation persistence and management
- **config.py**: Configuration loading and management
- **models.py**: Model definitions and selection
- **templates.py**: Template system implementation
- **context.py**: Reference file and KB handling
- **security.py**: Input validation and security

### Data Storage
- **Conversations**: `~/.config/dejavu2-cli/conversations/`
- **User Config**: `~/.config/dejavu2-cli/config.yaml`
- **Templates**: `Agents.json` in project directory
- **Models**: `Models.json` with model definitions

## Key Benefits

1. **Unified Interface**: Single CLI for all major LLMs
2. **Context Persistence**: Maintain conversations across sessions
3. **Flexibility**: Switch models mid-conversation, adjust parameters on-the-fly
4. **Automation Ready**: Designed for scripting and workflow integration
5. **Professional Features**: Templates, logging, security, error handling
6. **Cost Efficiency**: Compare models easily, use the right tool for each task

## Current Version & Status

**Version**: 0.8.30 (Active Development)

The project is actively maintained with regular updates for new models and features. It provides a production-ready solution for unified LLM access in command-line environments.

---

For detailed documentation, see the [docs/PURPOSE-FUNCTIONALITY-USAGE.md](docs/PURPOSE-FUNCTIONALITY-USAGE.md) file.

#fin