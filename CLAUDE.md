# DejaVu2-CLI Project Guide

## Commands & Development
- Run CLI: `./dejavu2-cli "Your query" [options]` or `./dv2 "query" [options]`
- Model selection: `./dejavu2-cli "query" -m claude-3-5-sonnet`
- List models: `./dejavu2-cli --list-models` `--list-template-names` `--status`
- Update models: `python Models/update_anthropic_models.py` or `python Models/update_openai_models.py`
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `./run_tests.sh` or `python -m pytest`
- Run specific tests: 
  - Categories: `./run_tests.sh --unit|--integration|--functional`
  - Single test: `python -m pytest tests/path/to/test_file.py::TestClass::test_function -v`
  - With coverage: `./run_tests.sh --coverage`

## Code Style
- Python: 2-space indentation, 100 char line limit, shebang `#!/usr/bin/env python3`
- Imports: Group by stdlib → third-party → local, alphabetically sorted within groups
- Types: Use typing module annotations (Dict, List, Optional, Any, etc.)
- Naming: snake_case for variables/functions, PascalCase for classes
- Docstrings: Google style for all public APIs with Args/Returns/Raises sections
- Error handling: Specific exception types, proper logging, avoid bare except
- Logging: Use logging module with appropriate levels, not print()
- Scripts must end with `#fin` on last line

## Architecture
- CLI: Click-based Python CLI supporting multiple LLM providers
- Config: YAML files (defaults.yaml), Models.json for model definitions
- Environment: Set `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` for API access
- Testing: pytest with fixtures in conftest.py
- Security: NEVER store API keys in code or config files

#fin