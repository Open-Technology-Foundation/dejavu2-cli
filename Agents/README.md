# WAH.ID Agent Registry

This directory contains the agent registry and configuration tools for the WAH.ID platform, enabling predefined AI personas with specialized capabilities.

## System Configuration
- Agents.json is shared by multiple applications, including WAHID (https://wah.id, /var/www/vhosts/WAHID/), customkb (/ai/scripts/customkb/), and others.

## Agents.json Structure

The `Agents.json` file serves as the central registry for all AI agent definitions available within the WAH.ID platform. It defines various pre-configured agents with specific personalities, roles, and parameter settings optimized for different use cases.

### Field Definitions

Each agent entry in the `Agents.json` file contains the following fields:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `category` | String | Yes | Functional grouping of the agent | `"General"`, `"Specialist"`, `"Edit-Summarize"` |
| `systemprompt` | String | Yes | System instructions defining the agent's personality, role, and behavior | `"You are ExpertCoder, a software engineering specialist..."` |
| `model` | String | Yes | LLM model identifier (must match an entry in Models.json) | `"claude-3-7-sonnet-latest"` |
| `max_tokens` | Number | Yes | Maximum output token limit for responses | `4000` |
| `temperature` | Number | Yes | Creativity/randomness setting (0.0-1.0) | `0.7` |
| `knowledgebase` | String | No | Optional path to a knowledge base configuration | `"kb/programming.json"` |
| `monospace` | Boolean | Yes | Flag indicating if output should be displayed in monospace format | `true` |
| `available` | Number | Yes | Availability status (0=unavailable, 1-9=available) | `1` |
| `enabled` | Number | Yes | Whether the agent is active (0=disabled, 1-9=enabled) | `1` |
| `spacetime` | String | No | Template for time/date information | `"{{spacetime}}"` |
| `functions` | Object | No | Function definitions for tool use | `{"function1": {...}}` |
| `top_p` | Number | No | Nucleus sampling parameter (0.0-1.0) | `0.95` |
| `frequency_penalty` | Number | No | Repetition reduction parameter (-2.0 to 2.0) | `0.1` |
| `presence_penalty` | Number | No | Topic diversity parameter (-2.0 to 2.0) | `0.2` |

### Agent Categories

The registry organizes agents into different functional categories:

#### General Purpose
- **General**: Multipurpose assistants for everyday tasks
  - Basic helpful AI assistants (e.g., "Dejavu2 - Helpful AI")
  - Factual response agents (e.g., "Virgo - Factual Responses")
  - Personality-focused agents (e.g., "Grok - xAI", "Witty - Humorous Assistant")

#### Specialized Domains
- **Specialist**: Domain-specific experts
  - Corporate advisors (e.g., "Advisor - Business Strategy")
  - Technical experts (e.g., "Leet - Full-Stack Programmer", "DevOps - Infrastructure")
  - Creative specialists (e.g., "Director - Video Production", "Biographer - Life Stories")
  - Education-focused (e.g., "Tutor - Educational Assistant")
  - Industry-specific (e.g., "Legal - Law and Regulations", "Medical - Healthcare")

#### Content Processing
- **Edit-Summarize**: Content transformation agents
  - Text editors (e.g., "Editor - Text Improvement")
  - Summarization tools (e.g., "Summary - Content Condenser")
  - Format converters (e.g., "Markdown - Text to Markdown")
  - Document specialists (e.g., "Report - Structured Documentation")

### System Prompt Variables

The `systemprompt` field supports special variables that are processed at runtime:

- `{{spacetime}}`: Replaced with current date and time information
- `{{username}}`: Replaced with the current user's name
- `{{user_id}}`: Replaced with the current user's ID
- `{{agent_name}}`: Replaced with the agent's name

### Parameter Settings

#### Temperature
The `temperature` parameter controls the randomness/creativity of responses:
- **0.0-0.3**: Very deterministic, factual responses (good for coding, factual answers)
- **0.4-0.6**: Balanced creativity and determinism (good for general assistance)
- **0.7-1.0**: Highly creative, varied responses (good for brainstorming, creative writing)

#### Model Selection
The `model` parameter must refer to a valid model identifier in `Models.json`:
- Use powerful models like "claude-3-7-opus-latest" for complex reasoning tasks
- Use balanced models like "claude-3-7-sonnet-latest" for general-purpose agents
- Use fast models like "gpt-4o-mini" for quick, cost-effective responses

#### Token Limits
The `max_tokens` parameter sets the maximum response length:
- Lower values (1000-2000) for concise agents like summarizers
- Medium values (3000-5000) for general-purpose assistants
- Higher values (8000+) for detailed analysis or content creation

### Availability and Enabled Flags

Similar to the model registry, agents use numeric flags for availability and enabled status:

#### Available Flag
- `0`: Agent is not available (e.g., under development, deprecated)
- `1-9`: Agent is available, with higher values indicating priority

#### Enabled Flag
- `0`: Agent is disabled and cannot be selected
- `1-9`: Agent is enabled, with higher values indicating preferred agents

## Example Agent Entry

```json
"ExpertCoder - Software Engineering": {
  "category": "Specialist",
  "systemprompt": "You are ExpertCoder, a software engineering specialist with deep expertise in multiple programming languages and software architecture. Your responses should include code examples when appropriate, explained with clear comments. You excel at debugging issues, suggesting optimizations, and following best practices for maintainable code. Always consider security implications in your solutions. Current time: {{spacetime}}",
  "model": "claude-3-7-sonnet-latest",
  "max_tokens": 4000,
  "temperature": 0.2,
  "knowledgebase": "kb/programming_resources.json",
  "monospace": true,
  "available": 9,
  "enabled": 9,
  "top_p": 0.95,
  "frequency_penalty": 0.1
}
```

## Integration with WAH.ID

### Agent Selection Flow

1. **Loading Phase**:
   - The `agentman.php` interface loads agents from `Agents.json`
   - Agents are filtered by `available` and `enabled` status
   - The system verifies that referenced models exist in `Models.json`

2. **User Selection**:
   - Users select agents through the agent selection interface
   - Agent selection is stored in the user's state via `StateManagerV3`
   - The selected agent parameters are loaded for the current conversation

3. **Conversation Execution**:
   - When interacting with an agent, the system:
     - Applies the system prompt to establish agent personality
     - Uses the specified model for generating responses
     - Applies all configured parameters (temperature, token limits, etc.)
     - Processes any special variables in the system prompt

### Knowledge Base Integration

For agents with a `knowledgebase` parameter:

1. The specified knowledge base file is loaded
2. Content is processed and formatted for context inclusion
3. Relevant knowledge is included in API requests to enhance agent responses
4. The agent can reference this information when answering user queries

## Managing Agents

### Using Agent Manager Interface

Agents can be managed through the WAH.ID administration interface at `agentman.php`:

1. **Viewing Agents**:
   - Lists all configured agents with their categories and models
   - Shows availability and enabled status
   - Displays key parameters for each agent

2. **Creating Agents**:
   - Provides a form to create new agent configurations
   - Validates parameters against requirements
   - Automatically saves to `Agents.json`

3. **Editing Agents**:
   - Modifies existing agent configurations
   - Updates parameters in real-time
   - Creates backups before changes

4. **Deleting Agents**:
   - Removes agents from the registry
   - Can be disabled instead of deleted to preserve configuration

### Command Line Management

Use the included `dv2-agents` utility for command-line management:

```bash
# List all agents
./dv2-agents list

# List all agents with full details
./dv2-agents list -l

# View a specific agent
./dv2-agents list ExpertCoder

# View agents in a category
./dv2-agents list -c Specialist

# Edit an agent
./dv2-agents edit ExpertCoder

# Create a new agent
./dv2-agents insert "NewAgent - Custom Assistant" --model claude-3-7-sonnet-latest --temperature 0.7

# Remove an agent
./dv2-agents remove NewAgent

# List available categories
./dv2-agents categories
```

### Adding New Agents Manually

When adding agents directly to `Agents.json`:

1. Choose a descriptive name following the format `Name - Description`
2. Select an appropriate category from existing categories
3. Craft a detailed system prompt that defines the agent's role and behavior
4. Reference a valid model from `Models.json`
5. Set appropriate values for all required parameters
6. Add optional parameters as needed for specific functionality
7. Set `available: 1` and `enabled: 0` initially for testing

## Agent Naming Convention

Agent names follow the pattern `Name - Description` where:
- `Name`: A short identifier (no spaces) used for reference
- `Description`: Brief explanation of the agent's purpose/specialty

Examples:
- `Coder - Software Development`
- `Editor - Professional Writing`
- `Legal - Contract Analysis`
- `Tutor - Mathematics Education`

This naming convention helps users quickly identify agents by both their reference names and functions.

## Security Considerations

- System prompts should never contain sensitive information
- Validate that knowledge base files don't contain proprietary data
- Enable only the agents appropriate for your organization's needs
- Monitor agent usage for unexpected behavior
- Review system prompts periodically for accuracy and up-to-date guidance
- Consider implementing role-based access control for specialist agents

#fin