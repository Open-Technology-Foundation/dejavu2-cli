# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Agent Management
- List all agents: `./dv2-agents list`
- List with details: `./dv2-agents list -l`
- View specific agent: `./dv2-agents list "AgentName"`
- List by category: `./dv2-agents list -c Specialist`
- Edit agent: `./dv2-agents edit "AgentName"`
- Create new agent: `./dv2-agents insert "NewAgent - Description" --model claude-3-7-sonnet-latest --temperature 0.7`
- Remove agent: `./dv2-agents remove "AgentName"`
- List categories: `./dv2-agents categories`

### Utility Scripts
- Create agent aliases: `./dv2-agents-aliases`
- Python implementation: `python dv2-agents.py [commands]`

## Code Standards
- Python: 2-space indentation, shebang `#!/usr/bin/env python3`
- JSON: Valid formatting required for Agents.json
- Scripts must end with `#fin` on last line
- Agent names follow format: `Name - Description`

## Agent Configuration Structure

### Required Fields
- `category`: Agent grouping (General/Specialist/Edit-Summarize)
- `systemprompt`: Core instructions defining agent behavior
- `model`: LLM model identifier from Models.json
- `max_tokens`: Maximum output token limit
- `temperature`: Creativity setting (0.0-1.0)
- `monospace`: Output formatting flag
- `available`: Availability status (0=unavailable, 1-9=available)
- `enabled`: Active status (0=disabled, 1-9=enabled)

### Optional Fields
- `knowledgebase`: Path to knowledge base configuration
- `spacetime`: Template for time/date info (`{{spacetime}}`)
- `top_p`: Nucleus sampling parameter
- `frequency_penalty`: Repetition reduction (-2.0 to 2.0)
- `presence_penalty`: Topic diversity (-2.0 to 2.0)

## Agent Categories
- **General**: Multipurpose assistants (Dejavu2, Grok, Sarki, Virgo)
- **Specialist**: Domain experts (askOkusi, Bio, Leet, Medical, Legal)
- **Edit-Summarize**: Content processors (Editor, Summariser, TRANS, X_Post)

## Development Guidelines

### Adding New Agents
1. Follow naming convention: `Name - Short Description`
2. Select appropriate category
3. Craft detailed system prompt with clear role/behavior
4. Reference valid model from parent Models.json
5. Set temperature based on use case (lower for factual, higher for creative)
6. Set `available: 1` and `enabled: 0` for initial testing

### System Prompt Variables
- `{{spacetime}}`: Current date/time placeholder
- `{{username}}`: User's name (if available)
- `{{user_id}}`: User identifier
- `{{agent_name}}`: Agent's name

### Temperature Guidelines
- **0.0-0.3**: Factual, deterministic (coding, analysis)
- **0.4-0.6**: Balanced (general assistance)
- **0.7-1.0**: Creative (brainstorming, writing)

### Knowledge Base Integration
- KB paths relative to `/var/lib/vectordbs/`
- Format: `/var/lib/vectordbs/domain/config.cfg`
- Used for enhanced context in specialized domains

## Testing Agents
1. Create agent with `enabled: 0` for testing
2. Use parent dejavu2-cli to test: `../dv2 "test query" -T "AgentName"`
3. Monitor performance and adjust parameters
4. Set `enabled: 1` when ready for production

## File Structure
```
Agents/
├── Agents.json          # Main agent registry
├── README.md           # Detailed documentation
├── CLAUDE.md          # This file
├── dv2-agents         # Main management script
├── dv2-agents.py      # Python implementation
├── dv2-agents-aliases # Alias creation utility
└── requirements.txt   # Python dependencies
```

#fin