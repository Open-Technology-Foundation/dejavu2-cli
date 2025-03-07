# DejaVu2-CLI Agents Registry

This directory contains the agents registry and tools for the DejaVu2-CLI application.

## Agents.json

The `Agents.json` file serves as the central registry for AI agent definitions in the DejaVu2-CLI application. It defines various pre-configured agents with specific personalities, roles, and parameter settings for different use cases.

### Structure

Each agent entry in the JSON file contains the following fields:

- **category**: Groups agents by function (e.g., "General", "Specialist", "Edit-Summarize")
- **systemprompt**: The system instructions that define the agent's personality, role, and behavior
- **model**: The LLM model to use (references a model from `Models.json`)
- **max_tokens**: Maximum output token limit for responses
- **temperature**: Creativity/randomness setting (0.0-1.0)
- **knowledgebase**: Optional path to a knowledge base configuration for enhanced context
- **monospace**: Boolean flag to indicate if output should be displayed in monospace format
- **spacetime**: Optional template for time/date information (usually `{{spacetime}}`)

### Agent Categories

The registry organizes agents into different categories:

1. **General**: Multipurpose assistants for everyday tasks
   - Basic helpful AI assistants
   - Factual response agents
   - Personality-focused agents (humorous, sarcastic, etc.)

2. **Specialist**: Domain-specific experts
   - Corporate advisors
   - Medical specialists
   - Philosophical agents
   - Technical experts (programming, engineering)
   - Creative specialists (video creation, biography)

3. **Edit-Summarize**: Content transformation agents
   - Text editors and reformatters
   - Summarization tools
   - Format converters (text to markdown)
   - Social media content creators
   - Journalistic style editors

### Usage in Code

The Agents.json registry is used throughout the DejaVu2-CLI application:

1. **Agent Selection**:
   - Agents are loaded from Agents.json into memory
   - User agent requests are matched by name
   - Agent parameters are applied to the conversation

2. **Model Configuration**:
   - The specified model is loaded from Models.json
   - Temperature and max_tokens are applied to API calls
   - Knowledge base integration is configured if specified

3. **Conversation Context**:
   - The systemprompt defines the agent's personality and behavior
   - Special variables like {{spacetime}} are processed
   - Knowledge base data is integrated if specified

## Utilities

### dv2-agents

The `dv2-agents` script provides a command-line interface for managing agents defined in Agents.json.

Usage examples:

```bash
# List all agents
./dv2-agents list

# List all agents with full details
./dv2-agents list -l

# View a specific agent
./dv2-agents list Leet

# View a specific agent with full details
./dv2-agents list -l Leet

# List all agent categories
./dv2-agents categories

# Edit an agent
./dv2-agents edit Leet

# Create a new agent
./dv2-agents insert "NewAgent - Custom Assistant" --model gpt-4o --temperature 0.7

# Remove an agent
./dv2-agents remove NewAgent
```

### Adding New Agents

When adding new agents to the registry:

1. Choose a descriptive name following the format "Name - Description"
2. Select an appropriate category
3. Craft a detailed systemprompt that defines the agent's role and behavior
4. Choose an appropriate model from Models.json
5. Set reasonable values for max_tokens and temperature
6. Specify a knowledge base path if needed
7. Set monospace to true if the output should be in monospace format

Example:
```json
"NewAgent - Custom Assistant": {
  "category": "General",
  "systemprompt": "You are NewAgent, a helpful assistant with specific expertise. You help users by...",
  "model": "claude-3-7-sonnet-latest",
  "max_tokens": 4000,
  "temperature": 0.4,
  "knowledgebase": "",
  "monospace": false
}
```

### Agent Naming Convention

Agent names follow the pattern `Name - Description` where:
- `Name`: A short identifier (no spaces)
- `Description`: Brief explanation of the agent's purpose

For example: `Leet - Full-Stack Programmer`

This naming convention helps users quickly identify agents by both their names and functions.

