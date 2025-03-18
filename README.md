# dejavu2-cli 

A powerful command-line interface for interacting with various Large Language Models (LLMs) including OpenAI, Anthropic Claude, Google Gemini, and local models via Ollama.

## Overview

`dejavu2-cli` (`dv2` for short) is a versatile command-line tool designed for executing one-shot queries to multiple language models, including those from OpenAI, Anthropic, Google, and local models via the Ollama server.

The `dv2` tool allows users to interact with LLMs efficiently by providing a range of customizable options, and supports context inclusion through reference files and `customKB` knowledge bases. The tool seamlessly handles different model APIs, response formats, and maintains conversation history for contextual interactions.

## Features

- **Multi-Model Support**: Seamlessly switch between different LLMs such as GPT-4, Claude variants, Gemini models, and LLaMA models by specifying the model name or using predefined aliases.
- **Conversation History**: Maintain context across multiple interactions with saved conversation history, allowing for follow-up questions and continued discussions.
- **Customizable Parameters**: Fine-tune responses by adjusting parameters like temperature, maximum tokens, and system prompts directly from the command line.
- **Contextual Inputs**: Enhance queries by including content from reference text files or customKB knowledge bases, allowing for richer and more informed responses.
- **Template Management**: Utilize user-defined templates in JSON format to initialize query parameters, ensuring consistency and saving time on repetitive tasks.
- **Configuration Loading**: Automatically load default settings and user-specific configurations from YAML files, with the ability to override them via command-line options.
- **Listing and Editing Tools**: List available models, templates, customKB knowledge bases, and conversations. Edit configuration and template files directly from the command line.
- **Status Display**: Preview the current state of all arguments, options, and conversation context before executing a query.
- **Model-Specific Parameter Handling**: Automatically adjusts parameters for different model types (like OpenAI's O1/O3 models) to ensure compatibility.
- **Robust API Integration**: Handles various API response formats, particularly for Ollama chat endpoints, with graceful fallback mechanisms for different JSON structures.
- **Metadata Tracking**: Captures and logs useful metadata from model responses for performance monitoring and debugging.

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
- [Authors](#authors)

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

   Strongly recommended to set up a virtual environment first.
   
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
   - **Remote Ollama Models**: Can connect to remote Ollama instances with special handling for models with colons in their names (like "gemma3:4b").

#### Ollama API Integration

The tool includes robust handling for Ollama API responses, particularly for the chat endpoint:

- Supports both local (http://localhost:11434/api/chat) and remote (https://ai.okusi.id/api/chat) Ollama servers
- Handles streaming and non-streaming JSON responses with appropriate parsing
- Processes various response formats from the chat endpoint:
  ```json
  {
    "model": "llama3.2",
    "message": {
      "role": "assistant",
      "content": "Response text..."
    },
    "done": true
  }
  ```
- Extracts and logs metadata from completed responses:
  - `total_duration`: Total processing time in milliseconds
  - `load_duration`: Time taken to load the model
  - `prompt_eval_count`: Number of tokens in the prompt
  - `eval_count`: Number of tokens generated
- Provides graceful error handling for various Ollama API error responses

4. **Ensure Ollama Server is Running** (Optional):

   - If you plan to use local LLaMA-based models, make sure the [Ollama](https://ollama.ai) server is installed and running.

5. **Run the Script**:

   ```bash
   dejavu2-cli "Your query here"
   # Or use the shorthand
   dv2 "Your query here"
   ```

## Usage

Run `dv2` with your query and desired options:

```bash
dv2 "Your query here" [options]
```

To view all available options:

```bash
dv2 --help
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

### Conversation Options

- `-c, --continue`  
  Continue the most recent conversation, maintaining context from previous exchanges.

- `-C, --conversation TEXT`  
  Load a specific conversation by ID to continue an earlier interaction.

- `-x, --list-conversations`  
  List all saved conversations with their IDs, titles, and other metadata.

- `-X, --delete-conversation TEXT`  
  Delete a specific conversation by ID.

- `-n, --new-conversation`  
  Start a new conversation even when continuing would be possible.
  
- `-i, --title TEXT`  
  Set a title for a new conversation (otherwise one will be auto-generated).
  
- `-e, --export-conversation TEXT`  
  Export a conversation to markdown format. Use "current" for the active conversation or specify a conversation ID.

- `-f, --export-path TEXT`  
  Specify the path to save the exported markdown file (defaults to current directory).
  
- `-O, --stdout`  
  Output the exported conversation directly to stdout instead of saving to a file.
  
- `-W, --list-messages CONVERSATION_ID`  
  List all messages in a conversation with their indices and content previews, useful for identifying specific messages to remove.

- `--remove-message ('CONVERSATION_ID', 'MESSAGE_INDEX')`  
  Remove a single message from a conversation. Use `--list-messages` first to find the correct indices.

- `--remove-pair ('CONVERSATION_ID', 'USER_MESSAGE_INDEX')`  
  Remove a user-assistant message pair. The index must point to a user message that is followed by an assistant message.

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

### Conversation Storage

Conversations are stored as JSON files in:

```
~/.config/dejavu2-cli/conversations/
```

Each JSON file contains:
- Conversation metadata (id, title, created/updated timestamps)
- Model configuration (model, temperature, max_tokens)
- Complete message history (including system prompts)

This allows for persistent context across sessions and detailed conversation tracking.

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
dv2 "Explain quantum computing in simple terms." -T "DéjàVu2 - Helpful AI"
```

## Examples

### Basic Query

```bash
dv2 "What is the capital of France?"
```

### Using a Template

```bash
dv2 "Provide a summary of the latest news." -T "Summariser - Summary Machine"
```

### Specifying a Model and Adjusting Temperature

```bash
dv2 "Generate a creative story about a flying car." -m gpt4o -t 0.9
```

### Including Reference Files

```bash
dv2 "Analyze the following code." -r "script.py,helpers.py"
```

### Using Conversation History

Conversations keep track of your interactions with the model, including system prompts, queries, responses, and configuration details. Each conversation automatically stores metadata about the model, temperature, and other settings.

#### Starting Conversations

Start a new conversation:
```bash
dv2 "Tell me about quantum computing."
```

Start a new conversation with a specific title:
```bash
dv2 "Let's discuss space exploration." --title "Space Exploration Discussion"
```

#### Managing Conversations

List all saved conversations to see their IDs, titles, and message counts:
```bash
dv2 --list-conversations
```

Example output:
```
=== SAVED CONVERSATIONS ===
ID: 550e8400-e29b-41d4-a716-446655440000
Title: Quantum Computing Discussion
Messages: 4
Created: 2025-03-01 15:04
Updated: 2025-03-01 15:14
---
ID: 663a4911-c38b-42e5-9f23-889735512111
Title: Space Exploration Discussion
Messages: 2
Created: 2025-02-28 10:23
Updated: 2025-02-28 10:25
```

Examining a conversation with `--status` shows detailed information including metadata:
```
=== CONVERSATION ===
ID: 550e8400-e29b-41d4-a716-446655440000
Title: Quantum Computing Discussion
Messages: 4
Created: 2025-03-01 15:04
Last Updated: 2025-03-01 15:14

Metadata:
  model: claude-3-7-sonnet-latest
  temperature: 0.7
  max_tokens: 4000
  template: Dejavu2 - Helpful AI

Preview of last exchanges:
  User: Tell me about quantum computing
  Assistant: Quantum computing is a type of computing that...
  User: How does quantum entanglement work?
```

View or access a specific conversation by ID:
```bash
dv2 --conversation 550e8400-e29b-41d4-a716-446655440000 --status
```

Delete a conversation when you no longer need it:
```bash
dv2 --delete-conversation 550e8400-e29b-41d4-a716-446655440000
```

View all messages in a conversation with their indices and content previews:
```bash
dv2 --list-messages 550e8400-e29b-41d4-a716-446655440000
```

Example output:
```
=== MESSAGES IN CONVERSATION ===
ID: 550e8400-e29b-41d4-a716-446655440000
Title: Quantum Computing Discussion

Index: 0 | Role: system | 2025-03-01 15:04:00
Content: You are Dejavu2, a friendly and helpful general AI assistant...

Index: 1 | Role: user | 2025-03-01 15:04:10
Content: Tell me about quantum computing

Index: 2 | Role: assistant | 2025-03-01 15:04:15
Content: Quantum computing is a type of computing that...

Index: 3 | Role: user | 2025-03-01 15:14:22
Content: How does quantum entanglement work?

Index: 4 | Role: assistant | 2025-03-01 15:14:30
Content: Quantum entanglement is a phenomenon where two particles...
```

Remove a specific message from a conversation:
```bash
dv2 --remove-message 550e8400-e29b-41d4-a716-446655440000 3
```

Remove a user-assistant message pair (must specify the user message index):
```bash
dv2 --remove-pair 550e8400-e29b-41d4-a716-446655440000 1
```

#### Continuing Conversations

Continue the most recent conversation:
```bash
dv2 "How does quantum entanglement work?" -c
```

Continue a specific conversation by ID:
```bash
dv2 "I have more questions about this topic." --conversation 550e8400-e29b-41d4-a716-446655440000
```

Start a new conversation even if you have a recent one:
```bash
dv2 "Let's talk about something different." --new-conversation
```

#### Changing Parameters Mid-Conversation

You can change models or parameters while continuing a conversation:
```bash
# Continue with a different model
dv2 "Can you explain this more creatively?" -c -m "gpt4o" -t 0.7
```

The conversation metadata will automatically update to track these changes.

#### Exporting Conversations

Export a conversation to markdown format for sharing or archiving:
```bash
# Export the most recent conversation to a file
dv2 -e current

# Export a specific conversation by ID
dv2 -e 550e8400-e29b-41d4-a716-446655440000

# Export to a specific path/filename
dv2 -e current -f "~/Documents/quantum_discussion.md"

# Output directly to stdout (for piping or viewing)
dv2 -e current -O

# Output to stdout and pipe to less for paging
dv2 -e current -O | less

# Output to stdout and pipe to grep to search for specific content
dv2 -e current -O | grep "quantum"
```

The markdown export includes:
- Conversation metadata (title, ID, creation date)
- Model configuration (model, temperature, etc.)
- Complete message history with timestamps
- System prompts in collapsible sections
- Clear separation between message pairs with horizontal rules
- Proper formatting of role headers and timestamps

This improved formatting makes it easy to share conversations with others or store them in a more readable and visually organized format.

### Querying with a Knowledge Base

```bash
dv2 "Explain the company's financial position." -k "financial_reports"
```

### Displaying Full Status Information

```bash
dv2 "Your query here" --status -P
```

### Listing All Available Information

```bash
# List models with basic information
dv2 --list-models

# List models with detailed information
dv2 -A

# List all templates
dv2 -l all

# List template names only (concise)
dv2 -L

# List available knowledge bases
dv2 -K
```

### Editing Configuration Files

```bash
# Edit templates file
dv2 -E

# Edit defaults configuration
dv2 -D

# Edit models configuration
dv2 -d
```

### Using Different Model Types

```bash
# Using OpenAI GPT-4o model
dv2 "Explain quantum physics" -m gpt4o

# Using Anthropic Claude model
dv2 "Write a poem about nature" -m sonnet

# Using OpenAI o1-preview model
dv2 "Analyze this data" -m o1-preview

# Using local Ollama model (with Ollama server running)
dv2 "Translate to French" -m llama3
```

## Development

### Code Structure

The codebase has been modularized for better maintainability:

- **main.py**: Main CLI interface that connects all modules
- **utils.py**: General utility functions for string processing and date/time handling
- **config.py**: Configuration loading and file editing
- **templates.py**: Template management and display
- **models.py**: Model information handling and selection
- **context.py**: Reference files and knowledge base handling
- **llm_clients.py**: API client initialization and query functions for different LLM providers
- **display.py**: Status information display
- **conversations.py**: Conversation history storage and management

This modular approach makes the code easier to maintain, test, and extend with new features.

### Notable Components

#### LLM Clients Module

The `llm_clients.py` module is responsible for handling all interactions with LLM APIs:

- **OpenAI Client**: Handles both standard and O1/O3 models with their specific requirements
- **Anthropic Client**: Manages Claude model interactions with appropriate headers
- **Google Client**: Interfaces with Gemini models through the Google API
- **Ollama Client**: Supports both local and remote Ollama instances with robust response parsing

The Ollama client was recently updated to:
- Handle various response formats from the chat endpoint
- Support models with special naming patterns (like "gemma3:4b")
- Extract and log useful metadata from responses
- Provide meaningful error messages for different failure modes
- Handle both streaming and non-streaming responses

#### Conversations Module

The `conversations.py` module provides a sophisticated conversation management system:

- **Message Storage**: Stores conversations as JSON files with message history
- **State Management**: Tracks metadata like model, temperature, and creation time
- **Export Capabilities**: Convert conversations to markdown format for sharing
- **Context Maintenance**: Preserve context across multiple interactions

### Coding Standards

All Python code in this project follows these standards:
- **Indentation**: ALWAYS use 2-space indentation (never tabs or 4 spaces)
- **Line Length**: Maximum 100 characters per line
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Documentation**: Docstrings for all public functions, modules, and classes
- **Error Handling**: Consistent approach with meaningful error messages
- **Logging**: Structured logging with appropriate levels

### Testing

Run tests using the provided script:

```bash
./run_tests.sh
```

This will run unit, integration, and functional tests using pytest.

The test suite includes:
- **Unit Tests**: Testing individual functions and classes
- **Integration Tests**: Testing interactions between components
- **Functional Tests**: Testing end-to-end functionality

## License

This project is licensed under the GPL-3 License - see the [LICENSE](LICENSE) file for details.

## Authors

- Gary Dean
- Claude Code
- AI Community Contributors

*Current Version: 0.8.5*

