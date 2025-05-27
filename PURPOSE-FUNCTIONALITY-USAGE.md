# PURPOSE, FUNCTIONALITY, AND USAGE ANALYSIS

## I. Executive Summary

Dejavu2-cli is a sophisticated command-line interface that provides unified access to multiple Large Language Models (LLMs) from major providers including OpenAI, Anthropic Claude, Google Gemini, and Ollama. The project solves the critical problem of LLM ecosystem fragmentation by offering a single, consistent interface that abstracts away provider-specific complexities while maintaining full access to advanced features. It is designed for developers, researchers, and technical users who require programmatic access to AI capabilities with persistent conversation management, context integration, and enterprise-grade security.

## II. Core Purpose & Rationale (The "Why")

### Problem Domain
The modern LLM landscape is fragmented across multiple providers, each with distinct APIs, interfaces, authentication methods, and capabilities. Users must juggle different tools, learn multiple command syntaxes, manage separate configurations, and handle provider-specific quirks when working with different models. This fragmentation creates barriers to productivity, experimentation, and model comparison.

### Primary Goal(s)
The fundamental mission of dejavu2-cli is to **democratize and unify access to advanced LLMs** by creating a provider-agnostic interface that maintains consistency across all supported models while preserving their unique capabilities. The project aims to eliminate the overhead of multi-provider integration, enabling users to focus on their work rather than tooling complexity.

### Value Proposition
- **Unified Experience**: Single CLI syntax works across OpenAI GPT-4, Claude-3.5-Sonnet, Gemini, and local/remote Ollama models
- **Context Persistence**: Maintains conversation history and integrates reference files and knowledge bases seamlessly
- **Professional-Grade Features**: Template system, security validation, comprehensive configuration management, and robust error handling
- **Workflow Integration**: Designed for automation, scripting, and integration into development workflows
- **Cost and Time Efficiency**: Eliminates the need to learn and maintain multiple tools

### Intended Audience/Users
- **Software Developers**: Integrating AI capabilities into applications and automating development tasks
- **Data Scientists and Researchers**: Comparing model responses and conducting AI research
- **System Administrators**: Incorporating LLM capabilities into scripts and operational workflows
- **Technical Writers and Content Creators**: Leveraging AI for documentation and content generation
- **AI Enthusiasts and Power Users**: Experimenting with different models and advanced features

## III. Functionality & Capabilities (The "What" & "How")

### Key Features

**Multi-Provider LLM Access**
- **OpenAI Integration**: Full support for GPT-4, GPT-3.5, and specialized O1/O3 models with appropriate parameter handling
- **Anthropic Claude**: Complete Claude model family support with latest API capabilities
- **Google Gemini**: Native integration with Google's Generative AI API
- **Ollama Support**: Both local (localhost:11434) and remote Ollama instances for open-source models

**Conversation Management System**
- **Persistent History**: Conversations stored as structured JSON files in `~/.config/dejavu2-cli/conversations/`
- **Session Continuity**: Resume conversations with `-c` flag across sessions
- **Conversation Export**: Generate Markdown exports for documentation and sharing
- **History Management**: View, edit, and remove individual messages or entire conversations

**Context Enhancement Engine**
- **Reference Files**: Include multiple text files as context with `-r file1.txt,file2.txt`
- **Knowledge Base Integration**: Connect to customKB vector databases via `-k knowledge_base`
- **Dynamic Context Assembly**: Automatically formats and includes context in queries

**Template and Configuration System**
- **Agent Templates**: Predefined parameter sets stored in `Agents.json` for consistent usage patterns
- **Model Definitions**: Comprehensive model metadata in `Models.json` including context limits and costs
- **Configuration Hierarchy**: System defaults → user config → command-line overrides

### Core Mechanisms & Operations

**Modular Architecture**: The system employs a clean separation of concerns across specialized modules:
- **CLI Orchestration** (`main.py`): Click-based command-line interface with comprehensive option handling
- **Provider Abstraction** (`llm_clients.py`): Unified client interface that handles provider-specific API requirements
- **Conversation Engine** (`conversations.py`): JSON-based storage with metadata tracking and export capabilities
- **Model Management** (`models.py`): Model selection logic with alias resolution and parameter validation
- **Security Layer** (`security.py`): Input validation, subprocess hardening, and environment protection

**Request Processing Flow**:
1. **Input Validation**: Security checks and parameter validation
2. **Configuration Assembly**: Load defaults, apply templates, merge user overrides
3. **Context Gathering**: Assemble reference files and knowledge base content
4. **Model Selection**: Resolve aliases and initialize appropriate API client
5. **Query Execution**: Send formatted request with context to selected LLM
6. **Response Processing**: Handle streaming/non-streaming responses and format output
7. **Conversation Storage**: Persist conversation state with metadata

### Inputs & Outputs

**Inputs**:
- **Text Queries**: Natural language questions or prompts
- **Reference Files**: Text files, code, documentation, data files
- **Configuration Parameters**: Model selection, temperature, token limits, system prompts
- **Templates**: Predefined parameter sets from Agents.json
- **Knowledge Bases**: External vector databases for context enhancement

**Outputs**:
- **LLM Responses**: Formatted text responses from selected models
- **Conversation Files**: Structured JSON files with complete conversation history
- **Markdown Exports**: Human-readable conversation exports
- **Status Information**: Model details, token usage, configuration diagnostics
- **Error Messages**: Detailed error reporting with suggested remediation

### Key Technologies Involved
- **Python 3.x**: Core implementation language with comprehensive type annotations
- **Click Framework**: Professional CLI interface with rich option handling
- **HTTP Clients**: Provider-specific API integration (OpenAI, Anthropic, Google APIs)
- **JSON Processing**: Configuration and conversation storage
- **YAML Configuration**: Human-readable configuration files
- **Regular Expressions**: Pattern matching and validation
- **Subprocess Management**: Secure external command execution

### Scope
The project explicitly focuses on **command-line interaction with LLMs** and does not include:
- Web interfaces or GUI components
- Model training or fine-tuning capabilities
- Direct model hosting or serving infrastructure
- Real-time streaming interfaces beyond basic response display

## IV. Usage & Application (The "When," "How," Conditions & Constraints)

### Typical Usage Scenarios/Use Cases

**Development Workflow Integration**
```bash
# Code review assistance
dv2 "Review this code for potential issues" -r src/module.py -T "Code Reviewer"

# Documentation generation
dv2 "Generate API documentation for these functions" -r api.py -m gpt4o
```

**Research and Analysis**
```bash
# Compare model responses for research
dv2 "Analyze this dataset" -r data.csv -m claude-3-5-sonnet-latest
dv2 "Analyze this dataset" -r data.csv -m gpt-4o-latest

# Knowledge base queries
dv2 "What does the research say about quantum computing?" -k research_papers
```

**Automation and Scripting**
```bash
# Automated report generation
for file in reports/*.txt; do
    dv2 "Summarize this report" -r "$file" -T "Executive Summary" >> summary.md
done
```

**Interactive Problem Solving**
```bash
# Start a conversation
dv2 "Help me design a database schema for an e-commerce platform"

# Continue the conversation
dv2 "Now add user authentication requirements" -c

# Include additional context
dv2 "Consider these security requirements" -r security_spec.txt -c
```

### Mode of Operation

**Command-Line Interface**: The project operates exclusively as a CLI tool with multiple invocation methods:
- **Primary**: `./dejavu2-cli "query" [options]`
- **Shortcuts**: `./dv2 "query" [options]` or `./dv2c "query" [options]`
- **Direct Python**: `python main.py "query" [options]`

**Interactive Workflow**:
1. **Single Query**: Execute one-off questions with immediate responses
2. **Conversational**: Build multi-turn conversations with context persistence
3. **Batch Processing**: Integrate into scripts for automated processing
4. **Configuration Management**: Edit templates and manage conversation history

### Operating Environment & Prerequisites

**System Requirements**:
- **Operating System**: Linux, macOS, or Windows with Python 3.x support
- **Python Version**: Python 3.7 or later with pip package manager
- **Dependencies**: Listed in `requirements.txt` (Click, requests, PyYAML, etc.)

**API Access Requirements**:
- **OpenAI**: `OPENAI_API_KEY` environment variable
- **Anthropic**: `ANTHROPIC_API_KEY` environment variable  
- **Google**: `GOOGLE_API_KEY` environment variable
- **Ollama**: Running Ollama instance (local or remote)

**File System Requirements**:
- **Configuration Directory**: `~/.config/dejavu2-cli/` for user settings and conversation storage
- **Write Permissions**: Ability to create and modify files in the configuration directory

### Constraints & Limitations

**Functional Limitations**:
- **No Real-Time Collaboration**: Single-user tool without multi-user conversation sharing
- **Limited Multimedia Support**: Primarily text-based; no native image or audio processing
- **No Model Training**: Does not provide model fine-tuning or training capabilities
- **API Dependency**: Requires internet connectivity for cloud-based models

**Technical Constraints**:
- **Token Limits**: Bound by individual model context windows and rate limits
- **Memory Usage**: Large conversations and reference files can consume significant memory
- **Security Scope**: Input validation focused on preventing command injection; does not encrypt stored conversations

**Provider-Specific Constraints**:
- **O1/O3 Models**: Limited parameter support (no temperature control) due to OpenAI API restrictions
- **Rate Limiting**: Subject to provider-specific rate limits and quotas
- **Model Availability**: Dependent on provider model deployment and accessibility

### Integration Points

**File System Integration**:
- Reads reference files from any accessible path
- Outputs to configurable project directories
- Integrates with existing development workflows through file-based interaction

**Knowledge Base Integration**:
- Connects to customKB vector databases for enhanced context
- Supports external knowledge repositories via the `-k` parameter

**Environment Integration**:
- Respects standard environment variables for API keys
- Integrates with shell environments for scripting and automation
- Supports configuration file hierarchy for team/project settings

**Development Tool Integration**:
- Designed for integration into development workflows
- Supports batch processing for automated tasks
- Compatible with CI/CD pipelines through script execution

## V. Conclusion

Dejavu2-cli represents a mature, production-ready solution to the challenge of multi-provider LLM access. By providing a unified, secure, and feature-rich interface to the world's leading language models, it eliminates the friction that typically accompanies AI integration in technical workflows. The project's significance lies not just in its technical capabilities, but in its role as a force multiplier for developers, researchers, and technical users who can now leverage the full spectrum of available AI models without the overhead of managing multiple tools and interfaces. As the LLM ecosystem continues to evolve, dejavu2-cli provides a stable foundation that adapts to new providers and capabilities while maintaining a consistent user experience.