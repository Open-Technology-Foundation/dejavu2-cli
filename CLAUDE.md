# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands
- Run CLI: `./dejavu2-cli "query" [options]` or `./dv2 "query" [options]`
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `./run_tests.sh` or `python -m pytest`
- Test categories: `./run_tests.sh --unit|--integration|--functional`
- Single test: `python -m pytest tests/path/to/test_file.py::TestClass::test_function -v`
- With coverage: `./run_tests.sh --coverage`
- Update models: `python Models/update_anthropic_models.py` or `python Models/update_openai_models.py`

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
- **Configuration**: 
  - `defaults.yaml` - Default settings and paths
  - `Models.json` - Model definitions with aliases and parameters
  - `Agents.json` - Template definitions for parameter presets
- **Environment**: Requires `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` for respective models
- **Testing**: pytest with 3-tier structure (unit/integration/functional), fixtures in conftest.py
- **Conversation Storage**: JSON files in `~/.config/dejavu2-cli/conversations/`

## Development Notes
- Modular design separates concerns across specialized modules
- LLM clients handle provider-specific requirements (O1/O3 models need special parameter handling)
- Conversation system maintains context across sessions with metadata tracking
- Template system allows parameter presets for consistent usage patterns
- Knowledge base integration via customKB for context enhancement
- Robust error handling with meaningful messages and bypass options

## Development Guidelines

### Security Considerations
- **Input Validation**: All user inputs are validated through `security.py` module
- **API Key Management**: Never log or expose API keys; stored only in environment variables
- **File Path Validation**: All file operations use secure path validation
- **Subprocess Security**: External commands use secure subprocess handling
- **XML Safety**: User input is XML-escaped before inclusion in queries

### Performance Optimization
- **Lazy Loading**: Clients initialized only when needed
- **Response Caching**: Consider implementing for repeated queries
- **Memory Management**: Large conversations may require pagination
- **Concurrent Operations**: Use async patterns for multiple API calls when beneficial

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