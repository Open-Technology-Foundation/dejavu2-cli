# dejavu2-cli 

A powerful command-line interface for interacting with various 
Large Language Models (LLMs).

## Overview

`dejavu2-cli` (`dv2`) is a versatile command-line tool designed 
for executing one-shot queries to multiple language models, 
including those from OpenAI, Anthropic, and local LLaMA-based 
models via the Ollama server.

The `dv2` tool allows users to interact with LLMs efficiently by 
providing a range of customizable options, and supports context 
inclusion through reference files and `customKB` knowledge bases.

## Features

- **Multi-Model Support**: Seamlessly switch between different LLMs such as GPT-4, Claude variants, and LLaMA models by specifying the model name or using predefined shortcuts.
- **Customizable Parameters**: Fine-tune responses by adjusting parameters like temperature, maximum tokens, and system prompts directly from the command line.
- **Contextual Inputs**: Enhance queries by including content from reference text files or customKB knowledge bases, allowing for richer and more informed responses.
- **Template Management**: Utilize user-defined templates in YAML format to initialize query parameters, ensuring consistency and saving time on repetitive tasks.
- **Configuration Loading**: Automatically load default settings and user-specific configurations from YAML files, with the ability to override them via command-line options.
- **Listing and Editing Tools**: List available models, templates, and customKB knowledge bases. Edit configuration and template files directly from the command line using your preferred text editor.
- **Status Display**: Preview the current state of all arguments and options before executing a query to verify and adjust settings as needed.

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

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Configuration**:

   - Copy the default configuration to your user config directory:

     ```bash
     mkdir -p ~/.config/dejavu2-cli
     cp defaults.yaml ~/.config/dejavu2-cli/config.yaml
     ```

   - Edit `~/.config/dejavu2-cli/config.yaml` to add your API keys and customize settings.

     **Important**: Replace placeholder API keys with your actual keys from OpenAI and Anthropic.

     ```yaml
     api_keys:
       anthropic: "your_anthropic_api_key"
       openai: "your_openai_api_key"
     ```

4. **Ensure Ollama Server is Running** (Optional):

   - If you plan to use local LLaMA-based models, make sure the [Ollama](https://ollama.ai) server is installed and running.

5. **Run the Script**:

   ```bash
   dv2 "Your query here"
   ```

## Usage

Run `dv2` with your query and desired options:

```bash
.dv2 "Your query here" [options]
```

To view all available options:

```bash
dv2 --help
```

## Command-Line Options

- `-s, --systemprompt TEXT`  
  Set the system prompt for the AI assistant (e.g., "You are a helpful assistant.").

- `-m, --model TEXT`  
  Specify the LLM model to use (e.g., "gpt-4", "claude-2", "llama3.1").

- `-t, --temperature FLOAT`  
  Set the sampling temperature for the LLM (e.g., `0.7`); higher values make output more random.

- `-M, --max-tokens INTEGER`  
  Define the maximum number of tokens for the LLM to generate.

- `-r, --reference TEXT`  
  Include content from reference text files as context (comma-separated list of file paths).

- `-k, --knowledgebase TEXT`  
  Specify a customKB knowledge base to query for additional context.

- `-Q, --knowledgebase-query TEXT`  
  Define a query to send to the customKB knowledge base (defaults to the main query if not provided).

- `-K, --list-knowledge-bases`  
  List all available customKB knowledge bases.

- `-T, --template TEXT`  
  Use a template to initialize arguments (defined in `llm-Templates.yaml`).

- `-l, --list-template TEXT`  
  List details of all templates or a specific template.

- `-L, --list-template-names`  
  List the names of all available templates.

- `-E, --edit-templates`  
  Edit the `llm-Templates.yaml` file using the default editor.

- `-D, --edit-defaults`  
  Edit the `defaults.yaml` configuration file.

- `-S, --status`  
  Display the current state of all arguments and options.

- `--list-models`  
  List all available LLM models as defined in `defaults.yaml`.

## Configuration

### defaults.yaml

Contains default settings, model shortcuts, paths, API keys, and logging configurations.

```yaml
# defaults.yaml

# Command line defaults
defaults:
  template: Helpful AI
  systemprompt: You are a friendly and helpful AI Assistant.
  reference: ""
  model: sonnet
  temperature: 0.1
  max_tokens: 4000
  completions: 1
  knowledgebase: ""

# LLM model shortcuts
model_shortcuts:
  o1:           "o1-preview-2024-09-12"
  o1mini:       "o1-mini-2024-09-12"
  chatgpt:      "chatgpt-4o-latest"
  opus:         "claude-3-opus-20240229"
  sonnet:       "claude-3-5-sonnet-20240620"
  haiku:        "claude-3-haiku-20240307"
  gpt4o:        "gpt-4o-2024-08-06"
  gpt4omini:    "gpt-4o-mini"
  gpt4:         "gpt-4"
  gpt4turbo:    "gpt-4-turbo"
  gpt4preview:  "gpt-4-turbo-preview"
  llama3:       "llama3.1"

# Paths
paths:
  prgdir: ""  # Will be set programmatically
  template_path: llm-Templates.yaml
  customkb: /ai/scripts/customkb/customkb

# API clients
api_keys:
  anthropic: "your_anthropic_api_key"
  openai: "your_openai_api_key"

# Logging
logging:
  level: WARNING
  format: "%(levelname)s: %(message)s"

# Vector database path
vectordbs_path: /var/lib/vectordbs
```

### llm-Templates.yaml

Defines templates for initializing query parameters.

```yaml
Helpful AI:
  systemprompt: You are a friendly and helpful AI Assistant.
  model: sonnet
  max_tokens: 4000
  temperature: 0.55
  knowledgebase: ""
  monospace: false

# Add more templates as needed
```

### Setting Up Templates Directory

Ensure that `llm-Templates.yaml` is located in the same directory as the script or update the `template_path` in `defaults.yaml` accordingly.

## Templates

Templates allow you to predefine sets of parameters for common tasks. This is especially useful if you frequently use the same settings.

### Example Template Definition

```yaml
Helpful AI:
  systemprompt: You are a friendly and helpful AI Assistant.
  model: sonnet
  max_tokens: 4000
  temperature: 0.55
  knowledgebase: ""
  monospace: false
```

### Using a Template

```bash
dv2 "Explain quantum computing in simple terms." -T "Helpful AI"
```

## Examples

### Basic Query

```bash
dv2 "What is the capital of France?"
```

### Using a Template

```bash
dv2 "Provide a summary of the latest news." -T "Summarize - Expert Summariser"
```

### Specifying a Model and Adjusting Temperature

```bash
dv2 "Generate a creative story about a flying car." -m gpt4o -t 0.9
```

### Including Reference Files

```bash
dv2 "Analyze the following code." -r "script.py,helpers.py"
```

### Querying with a Knowledge Base

```bash
dv2 "Explain the company's financial position." -k "financial_reports"
```

### Listing Available Models

```bash
dv2 --list-models
```

### Editing Templates

```bash
dv2 --edit-templates
```

### Viewing Status

```bash
dv2 "Your query here" --status
```


