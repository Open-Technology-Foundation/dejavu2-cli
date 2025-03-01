# dejavu2-cli 

A powerful command-line interface for interacting with various 
Large Language Models (LLMs) including OpenAI, Anthropic Claude, Google Gemini, and local models via Ollama.

## Overview

`dejavu2-cli` (`dv2` for short) is a versatile command-line tool designed for executing one-shot queries to multiple language models, including those from OpenAI, Anthropic, and local LLaMA-based models via the Ollama server.

The `dv2` tool allows users to interact with LLMs efficiently by providing a range of customizable options, and supports context inclusion through reference files and `customKB` knowledge bases.

## Features

- **Multi-Model Support**: Seamlessly switch between different LLMs such as GPT-4, Claude variants, and LLaMA models by specifying the model name or using predefined aliases.
- **Customizable Parameters**: Fine-tune responses by adjusting parameters like temperature, maximum tokens, and system prompts directly from the command line.
- **Contextual Inputs**: Enhance queries by including content from reference text files or customKB knowledge bases, allowing for richer and more informed responses.
- **Template Management**: Utilize user-defined templates in JSON format to initialize query parameters, ensuring consistency and saving time on repetitive tasks.
- **Configuration Loading**: Automatically load default settings and user-specific configurations from YAML files, with the ability to override them via command-line options.
- **Listing and Editing Tools**: List available models, templates, and customKB knowledge bases. Edit configuration and template files directly from the command line using your preferred text editor.
- **Status Display**: Preview the current state of all arguments and options before executing a query to verify and adjust settings as needed.
- **Model-Specific Parameter Handling**: Automatically adjusts parameters for different model types (like OpenAI's O1/O3 models) to ensure compatibility.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Command-Line Options](#command-line-options)
- [Configuration](#configuration)
- [Templates](#templates)
- [Examples](#examples)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

## Installation

### Prerequisites

- **Python 3.7** or higher
- **pip** package manager

### Steps

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/Open-Technology-Foundation/dejavu2-cli.git
   cd dejavu2-cli
   ```

2. **Install Dependencies**:

   Recommended to set up a virtual environment first.
   
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:

   Create environment variables for your API keys:

   ```bash
   # Required for Anthropic models (claude-*)
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
   
   # Required for OpenAI models (gpt-*, o1-*, o3-*, etc.)
   export OPENAI_API_KEY="your_openai_api_key"
   
   # Required for Google/Gemini models (gemini-*)
   export GOOGLE_API_KEY="your_google_api_key"
   
   # No key needed for local Ollama models (llama-*)
   # Ensure Ollama server is running locally
   ```

   You can add these to your shell profile (`.bashrc`, `.zshrc`, etc.) for persistence.
   
   **Important**: Never store API keys in code or configuration files for security reasons.
   
   ### Special Note on Model Handling

   Models in different categories may have specific requirements or behaviors:

   - **OpenAI Models** (gpt-3.5-turbo, gpt-4, etc.): Standard approach with system and user prompts.
   - **OpenAI O1/O3 Models**: Use a different messaging format and require special parameter handling (`max_completion_tokens` instead of `max_tokens`; no temperature parameter).
   - **Claude Models**: Similar to OpenAI but with some differences in prompt handling.
   - **Google/Gemini Models**: Requires Google API key and uses a different client library.
   - **Local Models via Ollama**: Requires the Ollama server to be running locally on port 11434.

4. **Ensure Ollama Server is Running** (Optional):

   - If you plan to use local LLaMA-based models, make sure the [Ollama](https://ollama.ai) server is installed and running.

5. **Run the Script**:

   ```bash
   ./dejavu2-cli "Your query here"
   # Or use the shorthand
   ./dv2 "Your query here"
   ```

## Usage

Run `dv2` with your query and desired options:

```bash
./dv2 "Your query here" [options]
```

To view all available options:

```bash
./dv2 --help
```

## Command-Line Options

### Main Options

- `-V, --version`  
  Show version information and exit.

- `-T, --template TEXT`  
  Use a template to initialize arguments (defined in `Agents.json`).

- `-m, --model TEXT`  
  Specify the LLM model to use (e.g., "gpt-4o", "claude-3-7-sonnet-latest", "llama3.1"). Aliases like "sonnet" or "gpt4o" can also be used.

- `-s, --systemprompt TEXT`  
  Set the system prompt for the AI assistant (e.g., "You are a helpful assistant.").

- `-t, --temperature FLOAT`  
  Set the sampling temperature for the LLM (e.g., `0.7`); higher values make output more random.

- `-M, --max-tokens INTEGER`  
  Define the maximum number of tokens for the LLM to generate.

### Context Options

- `-r, --reference TEXT`  
  Include content from reference text files as context (comma-separated list of file paths).

- `-k, --knowledgebase TEXT`  
  Specify a customKB knowledge base to query for additional context.

- `-Q, --knowledgebase-query TEXT`  
  Define a query to send to the customKB knowledge base (defaults to the main query if not provided).

### Status and Information

- `-S, --status`  
  Display the current state of all arguments and options.

- `-P, --print-systemprompt`  
  Print the full system prompt when using `--status`.

### Listing Options

- `-a, --list-models`  
  List all available LLM models as defined in the `Models.json` file.

- `-A, --list-models-details`  
  List all available models with detailed information.

- `-l, --list-template TEXT`  
  List details of all templates or a specific template.

- `-L, --list-template-names`  
  List the names of all available templates.

- `-K, --list-knowledge-bases`  
  List all available customKB knowledge bases.

### Editing Options

- `-E, --edit-templates`  
  Edit the `Agents.json` file using the default editor or 'p'.

- `-D, --edit-defaults`  
  Edit the `defaults.yaml` configuration file.
  
- `-d, --edit-models`  
  Edit the `Models.json` file.

### Output Options

- `-p, --project-name TEXT`  
  The project name for recording conversations.

- `-o, --output-dir TEXT`  
  Directory to output conversation results to.

- `-g, --message <TEXT TEXT>...`  
  Add message pairs in the form: `-g role "message"` (e.g., `-g user "hello" -g assistant "hi"`).

## Configuration

### Configuration Files

The system uses three main configuration files:

1. **defaults.yaml**: Default settings and paths
2. **Models.json**: Model definitions and aliases
3. **Agents.json**: Template definitions

### defaults.yaml

Contains default settings, paths, and logging configurations.

```yaml
# defaults.yaml

# Command line defaults
defaults:
  template: Dejavu2 # This template, when specified, will override the values below
  systemprompt: You are a friendly and helpful AI Assistant.
  reference: ""
  model: sonnet
  temperature: 0.1
  max_tokens: 4000
  completions: 1
  knowledgebase: ""

# Paths
paths:
  prgdir: ""  # Will be set programmatically at runtime
  template_path: Agents.json
  customkb: /ai/scripts/customkb/customkb

# Logging
logging:
  level: DEBUG
  format: "%(levelname)s: %(message)s"

# Vector database path
vectordbs_path: /var/lib/vectordbs
```

### Models.json

Defines available models and their aliases. Each model entry contains:

```json
"claude-3-7-sonnet-latest": {
  "model": "claude-3-7-sonnet-latest",
  "alias": "sonnet",
  "parent": "Anthropic",
  "model_category": "LLM",
  "family": "claude3",
  "series": "claude3",
  "description": "Highest level of intelligence and capability with toggleable extended thinking",
  "training_data": "2024-10",
  "data_cutoff_date": "2024-10",
  "url": "https://api.anthropic.com/v1",
  "apikey": "ANTHROPIC_API_KEY",
  "context_window": 200000,
  "max_output_tokens": 128000,
  "token_costs": "$3.00/$15.00",
  "vision": 1,
  "available": 9,
  "enabled": 1
}
```

The `alias` field allows you to use shorthand names like "sonnet" instead of the full model name.

### Agents.json

Defines templates for initializing query parameters.

```json
{
  "DéjàVu2 - Helpful AI": {
    "category": "General",
    "knowledgebase": "",
    "max_tokens": 4000,
    "model": "claude-3-5-sonnet-latest", 
    "monospace": false,
    "systemprompt": "Your name is DéjàVu2. You are a friendly and helpful general AI assistant.",
    "temperature": 0.35
  }
}

```

## Templates

Templates allow you to predefine sets of parameters for common tasks. This is especially useful if you frequently use the same settings.

### Example Template Definition

```json
{
  "Summariser - Summary Machine": {
    "category": "Edit-Summarize",
    "knowledgebase": "",
    "max_tokens": 8000,
    "model": "claude-3-5-sonnet-latest",
    "monospace": false,
    "systemprompt": "You are a summarization machine. Summarize the key points of the user's text in a concise and insightful manner.",
    "temperature": 0.3
  }
}
```

### Using a Template

```bash
./dv2 "Explain quantum computing in simple terms." -T "DéjàVu2 - Helpful AI"
```

## Examples

### Basic Query

```bash
./dv2 "What is the capital of France?"
```

### Using a Template

```bash
./dv2 "Provide a summary of the latest news." -T "Summariser - Summary Machine"
```

### Specifying a Model and Adjusting Temperature

```bash
./dv2 "Generate a creative story about a flying car." -m gpt4o -t 0.9
```

### Including Reference Files

```bash
./dv2 "Analyze the following code." -r "script.py,helpers.py"
```

### Querying with a Knowledge Base

```bash
./dv2 "Explain the company's financial position." -k "financial_reports"
```

### Displaying Full Status Information

```bash
./dv2 "Your query here" --status -P
```

### Listing All Available Information

```bash
# List models with basic information
./dv2 --list-models

# List models with detailed information
./dv2 -A

# List all templates
./dv2 -l all

# List template names only (concise)
./dv2 -L

# List available knowledge bases
./dv2 -K
```

### Editing Configuration Files

```bash
# Edit templates file
./dv2 -E

# Edit defaults configuration
./dv2 -D

# Edit models configuration
./dv2 -d
```

### Using Different Model Types

```bash
# Using OpenAI GPT-4o model
./dv2 "Explain quantum physics" -m gpt4o

# Using Anthropic Claude model
./dv2 "Write a poem about nature" -m sonnet

# Using OpenAI o1-preview model
./dv2 "Analyze this data" -m o1-preview

# Using local Ollama model (with Ollama server running)
./dv2 "Translate to French" -m llama3
```