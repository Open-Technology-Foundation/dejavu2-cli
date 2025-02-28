# DejaVu2-CLI Project Guide

## Build/Test Commands
- Run CLI: `./dejavu2-cli "Your query" [options]`
- Run with specific model: `./dejavu2-cli "Your query" -m claude-3-5-sonnet`
- List models: `./dejavu2-cli --list-models`
- List templates: `./dejavu2-cli --list-template-names`
- Edit templates: `./dejavu2-cli --edit-templates`
- Edit config: `./dejavu2-cli --edit-defaults`
- View status: `./dejavu2-cli --status`

## Environment Setup
- Set API keys as environment variables:
  ```
  export ANTHROPIC_API_KEY="your-api-key"
  export OPENAI_API_KEY="your-api-key"
  ```

## Version Management
- Version is maintained in `version.py` as `__version__`
- Format follows semantic versioning (major.minor.patch)
- Use `version_updater.py` to increment version numbers:
  ```
  # Increment patch version (0.9.5 -> 0.9.6)
  ./version_updater.py 
  
  # Increment minor version (0.9.5 -> 0.10.0)
  ./version_updater.py minor
  
  # Increment major version (0.9.5 -> 1.0.0)
  ./version_updater.py major
  ```
- Version is accessible in code via `from version import __version__`

## Code Style Guidelines
- **Formatting**: Use 2-space indentation for all code
- **Imports**: Group imports (stdlib, third-party, local), sort alphabetically
- **Types**: Use type hints from typing module (Any, Dict, Optional, etc.)
- **Error Handling**: Use try/except blocks with specific exceptions
- **Logging**: Use the built-in logging module, not print statements
- **Variable Naming**: snake_case for variables/functions, PascalCase for classes
- **Documentation**: Docstrings for modules, classes, and functions
- **Error Messages**: Clear, informative messages with specific context

## Project Structure
- Python CLI tool using Click for argument parsing
- Supports multiple LLM providers (OpenAI, Anthropic, Ollama)
- Configuration via YAML files (defaults.yaml, llm-Templates.yaml)
- Model definitions in Models.json
- Integration with customkb for RAG capabilities