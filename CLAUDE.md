# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands
- Run CLI: `./dejavu2-cli "query" [options]` or `./dv2 "query" [options]`
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `./run_tests.sh` or `python -m pytest`
- Test categories: `./run_tests.sh --unit|--integration|--functional`
- Single test: `python -m pytest tests/path/to/test_file.py::TestClass::test_function -v`
- With coverage: `./run_tests.sh --coverage`
- Update models: `cd Models && ./dv2-models-update` or `./dv2-update-models`
- List models: `cd Models && ./dv2-models-list [filters]`
- Check outdated deps: `pip list --outdated`
- Update version: `./version_updater.py`

## Code Standards
- Python: 2-space indentation, 100 char line limit, shebang `#!/usr/bin/env python3`
- Imports: stdlib → third-party → local, alphabetically sorted within groups
- Types: Use typing module annotations (Dict, List, Optional, Any, etc.)
- Naming: snake_case for variables/functions, PascalCase for classes
- Docstrings: Google style for all public APIs with Args/Returns/Raises sections
- Error handling: Specific exception types, proper logging, avoid bare except
- Logging: Use logging module with appropriate levels, not print()
- Scripts must end with `#fin` on last line

## Architecture Overview
- **Main Entry**: `main.py` - Click-based CLI interface connecting all modules
- **Core Modules**: 
  - `llm_clients.py` - API clients for OpenAI, Anthropic, Google, Ollama
  - `conversations.py` - Conversation history storage and management
  - `config.py` - Configuration loading from YAML/JSON files
  - `models.py` - Model definitions and selection logic
  - `templates.py` - Template management for parameter presets
  - `context.py` - Reference files and knowledge base handling
  - `security.py` - Input validation and secure subprocess execution
  - `errors.py` - Custom exception hierarchy for precise error handling
- **Configuration**: 
  - `defaults.yaml` - Default settings and paths
  - `Models.json` - Model definitions with aliases and parameters
  - `Agents.json` - Template definitions for parameter presets
- **Environment**: Requires `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` for respective models
- **Testing**: pytest with 3-tier structure (unit/integration/functional), fixtures in conftest.py
- **Conversation Storage**: JSON files in `~/.config/dejavu2-cli/conversations/`

## Critical Module Interactions
- **Query Flow**: main.py → llm_clients.py → API → conversations.py (storage)
- **Security Layer**: All subprocess calls must go through security.py's SecureSubprocess
- **Model Resolution**: main.py → models.py (alias lookup) → llm_clients.py (API client)
- **Context Assembly**: main.py → context.py (files/KB) → XML formatting → LLM query
- **Error Propagation**: Custom exceptions from errors.py bubble up with context
- **Configuration Hierarchy**: defaults.yaml → user config → CLI args (override order)

## Development Notes
- Modular design separates concerns across specialized modules
- LLM clients handle provider-specific requirements (O1/O3 models need special parameter handling)
- Conversation system maintains context across sessions with metadata tracking
- Template system allows parameter presets for consistent usage patterns
- Knowledge base integration via customKB for context enhancement
- Robust error handling with meaningful messages and bypass options

## Ollama Integration Details
- **Local Server**: Default at http://localhost:11434/api/chat
- **Remote Server**: Supports https://ai.okusi.id/api/chat and custom endpoints
- **Model Names**: Special handling for colons (e.g., "gemma3:4b")
- **Response Formats**: Handles both streaming and non-streaming JSON
- **Metadata Extraction**: Captures total_duration, prompt_eval_count, eval_count
- **Error Handling**: Graceful fallback for different Ollama response formats

## Development Guidelines

### Security Considerations
- **Input Validation**: All user inputs are validated through `security.py` module
- **API Key Management**: Never log or expose API keys; stored only in environment variables
- **File Path Validation**: All file operations use secure path validation
- **Subprocess Security**: External commands use secure subprocess handling
- **XML Safety**: User input is XML-escaped before inclusion in queries

### Known Security Issues (Priority Fixes)
- **API Key Exposure**: Currently all API keys passed to subprocesses - filter based on need
- **Race Conditions**: No file locking on conversation saves - implement fcntl locking
- **XML Injection Risk**: Validate reference_string and knowledgebase_string before concatenation

### Performance Optimization
- **Lazy Loading**: Clients initialized only when needed
- **Response Caching**: Consider implementing for repeated queries
- **Memory Management**: Large conversations may require pagination
- **Concurrent Operations**: Use async patterns for multiple API calls when beneficial

### Performance Limitations
- **Large Conversations**: Entire history loaded into memory - implement 50 message limit
- **Synchronous API Calls**: Gemini model list blocks UI - add caching with TTL
- **File I/O**: Models.json/Agents.json loaded repeatedly - implement module-level caching

### Error Handling Philosophy
- **Specific Exceptions**: Use custom exception hierarchy from `errors.py`
- **Graceful Degradation**: Continue operation when possible (e.g., bypass KB errors)
- **User-Friendly Messages**: Provide actionable error messages
- **Detailed Logging**: Log full error context for debugging

### Adding New Features
1. **Plan**: Design the feature with existing architecture patterns
2. **Implement**: Follow code standards and use appropriate modules
3. **Test**: Add unit, integration, and functional tests
4. **Document**: Update docstrings, README.md, and this file
5. **Validate**: Ensure security considerations are addressed

## Troubleshooting Common Issues

### API Key Issues
- Verify environment variables are set: `echo $ANTHROPIC_API_KEY`
- Check key permissions and quotas with providers
- Use `--status` to verify key detection

### Model Selection Problems
- List available models: `./dv2 --list-models`
- Check Models.json for aliases and canonical names
- Verify provider API key for specific model families

### Conversation Issues
- List conversations: `./dv2 --list-conversations`
- Check conversation directory: `~/.config/dejavu2-cli/conversations/`
- Use `--new-conversation` to force fresh start

### Performance Issues
- Enable verbose logging: `--verbose --log-file performance.log`
- Check network connectivity for API calls
- Monitor token usage for large context windows
- Consider using smaller models for development/testing

### Development Environment
- Ensure Python 3.7+ compatibility
- Use virtual environment to avoid dependency conflicts
- Keep dependencies updated via `pip install -r requirements.txt --upgrade`

## File Structure Reference
```
dejavu2-cli/
├── main.py              # CLI entry point and orchestration
├── llm_clients.py       # LLM provider integrations
├── conversations.py     # Conversation management
├── config.py           # Configuration handling
├── models.py           # Model definitions and selection
├── templates.py        # Template system
├── context.py          # Reference files and KB integration
├── security.py         # Security validation
├── errors.py           # Custom exception hierarchy
├── utils.py            # Utility functions
├── display.py          # Output formatting
├── version.py          # Version information
├── defaults.yaml       # Default configuration
├── Models.json         # Model registry
├── Agents.json         # Template definitions
├── requirements.txt    # Python dependencies
├── run_tests.sh       # Test runner script
└── tests/             # Test suite
    ├── unit/          # Unit tests
    ├── integration/   # Integration tests
    └── functional/    # End-to-end tests
```

#fin