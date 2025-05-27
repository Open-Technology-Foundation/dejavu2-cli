#!/usr/bin/env python3
"""
Main module for dejavu2-cli that integrates all the modular components.

This is a connector module that brings together all the specialized modules
to create the complete functionality of the dejavu2-cli tool.
"""
import sys
import os
import time
import logging
import xml.sax.saxutils
from datetime import datetime
import click
from typing import Any, Dict, List, Optional

# Import modules from the project
from utils import setup_logging, post_slug, spacetime_placeholders
from config import load_config, edit_yaml_file, edit_json_file
from templates import get_template, list_templates, list_template_names
from models import get_canonical_model, list_models
from context import get_reference_string, get_knowledgebase_string, list_knowledge_bases
from llm_clients import get_api_keys, initialize_clients, query
from display import display_status
from conversations import ConversationManager
from errors import ConfigurationError, ModelError, TemplateError, ConversationError, ReferenceError, KnowledgeBaseError

# Constants
PRGDIR = os.path.dirname(os.path.realpath(__file__))
# Import version from version.py module
try:
    from version import __version__ as VERSION
except ImportError:
    VERSION = 'unknown'
    click.echo("Warning: version.py not found. Using 'unknown'.", err=True)

SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
DEFAULT_CONFIG_PATH = os.path.join(PRGDIR, 'defaults.yaml')
USER_CONFIG_PATH = os.path.expanduser('~/.config/dejavu2-cli/config.yaml')

# Setup logging will be done later with command line arguments
logger = None

# HELPER FUNCTIONS FOR MAIN COMMAND ====================================================

def setup_application(kwargs: Dict[str, Any]) -> tuple:
  """
  Setup logging, load configuration, and initialize paths.
  
  Args:
    kwargs: Command-line arguments parsed by Click
    
  Returns:
    Tuple of (logger, config, paths_dict)
  """
  # Set up logging first
  global logger
  # Handle verbose/quiet conflict - verbose takes precedence
  verbose = kwargs['verbose']
  quiet = kwargs['quiet'] and not verbose  # If verbose is True, quiet becomes False

  logger = setup_logging(
    verbose=verbose,
    log_file=kwargs['log_file'],
    quiet=quiet
  )

  # Create module-specific loggers for other modules
  config_logger = logging.getLogger('config')
  models_logger = logging.getLogger('models')
  templates_logger = logging.getLogger('templates')
  context_logger = logging.getLogger('context')
  llm_logger = logging.getLogger('llm_clients')
  display_logger = logging.getLogger('display')
  conv_logger = logging.getLogger('conversations')

  # Log startup information
  logger.info(f"Starting dejavu2-cli v{VERSION}")
  logger.debug(f"Python version: {sys.version}")
  logger.debug(f"Working directory: {os.getcwd()}")

  # Load configuration
  config = load_config(DEFAULT_CONFIG_PATH, USER_CONFIG_PATH)
  config_logger.debug(f"Configuration loaded from {config.get('config_file', 'defaults')}")

  # Set up paths
  template_path = os.path.join(PRGDIR, config['paths']['template_path'])
  models_json_path = os.path.join(PRGDIR, 'Models.json')
  customkb_executable = config['paths'].get('customkb', '/ai/scripts/customkb/customkb')
  vectordbs_path = config.get('vectordbs_path', '/var/lib/vectordbs')
  
  paths = {
    'template_path': template_path,
    'models_json_path': models_json_path,
    'customkb_executable': customkb_executable,
    'vectordbs_path': vectordbs_path
  }
  
  return logger, config, paths


def handle_utility_commands(kwargs: Dict[str, Any], paths: Dict[str, str]) -> bool:
  """
  Handle utility commands like editing files and listing templates/models.
  
  Args:
    kwargs: Command-line arguments
    paths: Dictionary of file paths
    
  Returns:
    True if a utility command was handled (should exit), False otherwise
  """
  if kwargs['edit_templates']:
    edit_json_file(paths['template_path'])
    return True

  if kwargs['edit_defaults']:
    edit_yaml_file(DEFAULT_CONFIG_PATH)
    return True

  if kwargs['list_template']:
    try:
      list_templates(paths['template_path'], kwargs['list_template'])
    except (ConfigurationError, TemplateError) as e:
      click.echo(f"Template error: {e}", err=True)
      sys.exit(1)
    return True

  if kwargs['list_template_names']:
    try:
      list_template_names(paths['template_path'])
    except (ConfigurationError, TemplateError) as e:
      click.echo(f"Template error: {e}", err=True)
      sys.exit(1)
    return True

  if kwargs['list_models']:
    list_models(paths['models_json_path'], False)
    return True

  if kwargs['list_models_details']:
    list_models(paths['models_json_path'], True)
    return True

  if kwargs.get('edit_models'):
    edit_json_file(paths['models_json_path'])
    return True

  if kwargs['list_knowledge_bases']:
    try:
      list_knowledge_bases(paths['vectordbs_path'])
    except KnowledgeBaseError as e:
      click.echo(f"Knowledge base error: {e}", err=True)
      sys.exit(1)
    return True
    
  return False


def handle_conversation_listing(conv_manager: ConversationManager) -> None:
  """
  Handle listing all saved conversations.
  
  Args:
    conv_manager: ConversationManager instance
  """
  conversations = conv_manager.list_conversations()
  if not conversations:
    click.echo("No saved conversations found.")
    return

  click.echo("\n=== SAVED CONVERSATIONS ===")
  for conv in conversations:
    created = datetime.fromisoformat(conv['created_at']).strftime("%Y-%m-%d %H:%M")
    updated = datetime.fromisoformat(conv['updated_at']).strftime("%Y-%m-%d %H:%M")
    click.echo(f"ID: {conv['id']}")
    click.echo(f"Title: {conv['title']}")
    click.echo(f"Messages: {conv['message_count']}")
    click.echo(f"Created: {created}")
    click.echo(f"Updated: {updated}")
    click.echo("---")


def handle_conversation_deletion(conv_manager: ConversationManager, conversation_id: str) -> None:
  """
  Handle deleting a specific conversation by ID.
  
  Args:
    conv_manager: ConversationManager instance for managing conversations
    conversation_id: Unique identifier of the conversation to delete
    
  Prints:
    Success message if conversation was deleted, or error if not found
  """
  if conv_manager.delete_conversation(conversation_id):
    click.echo(f"Conversation {conversation_id} deleted.")
  else:
    click.echo(f"Conversation {conversation_id} not found.")


def handle_message_operations(kwargs: Dict[str, Any], conv_manager: ConversationManager) -> bool:
  """
  Handle message-related operations (listing, removing messages).
  
  Args:
    kwargs: Command-line arguments
    conv_manager: ConversationManager instance
    
  Returns:
    True if a message operation was handled (should exit), False otherwise
  """
  # Handle listing messages in a conversation
  if kwargs['list_messages']:
    conv_id = kwargs['list_messages']
    messages = conv_manager.list_conversation_messages(conv_id)

    if not messages:
      click.echo(f"No messages found in conversation {conv_id} or conversation not found.")
      return True

    # Get conversation metadata for display
    conv = conv_manager.load_conversation(conv_id)
    title = "Untitled" if conv is None or conv.title is None else conv.title

    click.echo(f"\n=== MESSAGES IN CONVERSATION: {title} ===")
    click.echo(f"Conversation ID: {conv_id}")
    click.echo(f"Total messages: {len(messages)}")
    click.echo("\n{:<5} {:<10} {:<20} {:<50}".format("IDX", "ROLE", "TIMESTAMP", "PREVIEW"))
    click.echo("-" * 90)

    for msg in messages:
      # Format role with proper capitalization
      role = msg['role'].capitalize()
      # Add a marker for system messages
      if msg['is_system']:
        role += " *"

      # Format index with brackets for clarity
      idx = f"[{msg['index']}]"

      # Display in a table-like format with proper alignment
      click.echo("{:<5} {:<10} {:<20} {:<50}".format(
        idx, role, msg['timestamp'], msg['content_preview']
      ))
    return True

  # Handle removing a single message
  if kwargs['remove_message']:
    conv_id, msg_index = kwargs['remove_message']
    try:
      conv_manager.remove_message_at_index(conv_id, msg_index)
      click.echo(f"Message at index {msg_index} removed from conversation {conv_id}.")
    except ConversationError as e:
      click.echo(f"Conversation error: {e}", err=True)
      click.echo(f"Tip: Use -m {conv_id} to list all messages with their indices.")
    return True

  # Handle removing a message pair
  if kwargs['remove_pair']:
    conv_id, user_index = kwargs['remove_pair']
    try:
      conv_manager.remove_message_pair(conv_id, user_index)
      click.echo(f"Message pair starting at index {user_index} removed from conversation {conv_id}.")
    except ConversationError as e:
      click.echo(f"Conversation error: {e}", err=True)
      click.echo(f"Tip: Use -m {conv_id} to list all messages with their indices.")
    return True
    
  return False


def handle_conversation_export(kwargs: Dict[str, Any], conv_manager: ConversationManager) -> None:
  """
  Handle conversation export functionality.
  
  Args:
    kwargs: Command-line arguments
    conv_manager: ConversationManager instance
  """
  try:
    conv_id = None
    if kwargs['export_conversation'].lower() != 'current':
      conv_id = kwargs['export_conversation']

    # If "current" was specified but no active conversation exists,
    # load the most recent conversation
    if conv_id is None and not conv_manager.active_conversation:
      most_recent = conv_manager.get_most_recent_conversation()
      if most_recent:
        conv_manager.active_conversation = most_recent
        logger.debug(f"Loaded most recent conversation: {most_recent.id}")
      else:
        click.echo("No conversations found to export.")
        return

    # Check if we should output to stdout instead of a file
    if kwargs.get('stdout', False):
      # Export to stdout (no file)
      md_content = conv_manager.export_conversation_to_markdown(conv_id)
      click.echo(md_content)
      return

    # Otherwise, determine output path for file
    output_path = kwargs.get('export_path')
    if not output_path:
      # Generate a default filename if none provided
      if conv_id:
        filename = f"conversation_{conv_id}.md"
      else:
        # For current conversation, use the active conversation
        active_conv = conv_manager.active_conversation
        if active_conv:
          filename = f"conversation_{active_conv.id}.md"
        else:
          # This shouldn't happen now since we loaded the most recent above
          click.echo("No conversations found to export.")
          return

      # Use current directory if no path specified
      output_path = os.path.join(os.getcwd(), filename)

    # Export the conversation to file
    result = conv_manager.export_conversation_to_markdown(conv_id, output_path)
    click.echo(f"Conversation exported to: {result}")
  except ConversationError as e:
    click.echo(f"Conversation error: {e}", err=True)
    sys.exit(1)
  except Exception as e:
    click.echo(f"Unexpected error exporting conversation: {str(e)}", err=True)
    sys.exit(1)


def prepare_query_execution(kwargs: Dict[str, Any], config: Dict[str, Any], paths: Dict[str, str], conv_manager: ConversationManager) -> Dict[str, Any]:
  """
  Prepare all necessary components for query execution.
  
  Args:
    kwargs: Command-line arguments
    config: Configuration dictionary
    paths: Dictionary of file paths
    conv_manager: ConversationManager instance
    
  Returns:
    Dictionary containing all prepared query context
  """
  # Setup output directory
  output_dir = ''
  if kwargs['output_dir']:
    output_dir = kwargs.get('output_dir')
    os.makedirs(output_dir, exist_ok=True)

  # Setup project name
  project_name = ''
  if kwargs['project_name']:
    project_name = post_slug(kwargs['project_name'], '-', False, 24)
  if not project_name:
    project_name = 'noproj'

  # Setup active conversation
  active_conversation = setup_active_conversation(kwargs, conv_manager)

  # Read query texts
  query_texts = list(kwargs.get('query_text') or [])
  if not sys.stdin.isatty():
    stdin_input = sys.stdin.read()
    if stdin_input:
      query_texts.append(stdin_input)
  if not query_texts:
    click.echo(f"Require at least one query. Use '{SCRIPT_NAME} --help' for help.", err=True)
    sys.exit(1)

  # Determine knowledgebase query
  knowledgebase_query = kwargs.get('knowledgebase_query')
  if not knowledgebase_query and query_texts:
    knowledgebase_query = query_texts[0]

  # Process template and defaults
  process_template_and_defaults(kwargs, config, paths['template_path'])

  # Get messages from command line
  messages = list(kwargs.get('message', []))

  # Get model info and initialize clients
  canonical_model, model_parameters = setup_model_and_clients(kwargs, paths['models_json_path'])
  kwargs['model'] = canonical_model

  # Get API keys and initialize clients
  api_keys = get_api_keys()
  clients = initialize_clients(api_keys)

  # Validate API keys
  api_key_type = model_parameters.get('apikey', '')
  if api_key_type and not api_keys.get(api_key_type, ''):
    model_parameters['api_key_valid'] = False
  else:
    model_parameters['api_key_valid'] = True

  # Add conversation history to messages
  if active_conversation and active_conversation.messages:
    conversation_messages = active_conversation.get_messages_for_llm(include_system=False)
    if conversation_messages:
      logger.debug(f"Using {len(conversation_messages)} messages from conversation history")
      messages.extend(conversation_messages)

  # Process references and knowledge base
  reference_string, knowledgebase_string = process_reference_and_knowledge(
    kwargs, paths, api_keys, knowledgebase_query
  )

  return {
    'output_dir': output_dir,
    'project_name': project_name,
    'active_conversation': active_conversation,
    'query_texts': query_texts,
    'messages': messages,
    'model_parameters': model_parameters,
    'api_keys': api_keys,
    'clients': clients,
    'reference_string': reference_string,
    'knowledgebase_string': knowledgebase_string,
    'kwargs': kwargs
  }


def setup_active_conversation(kwargs: Dict[str, Any], conv_manager: ConversationManager):
  """
  Initialize or load the active conversation based on command-line arguments.
  
  This function handles three conversation scenarios:
  1. Load specific conversation by ID (--conversation)
  2. Continue most recent conversation (--continue)
  3. Create new conversation (default or --new-conversation)
  
  Args:
    kwargs: Command-line arguments containing conversation preferences
    conv_manager: ConversationManager instance for loading/creating conversations
    
  Returns:
    Conversation: Active conversation object ready for message exchange,
                 or None if no conversation could be established
    
  Side Effects:
    - Logs conversation loading/creation events
    - May exit with code 1 if specified conversation ID is not found
  """
  active_conversation = None

  # Load specific conversation if requested
  if kwargs['conversation_id']:
    active_conversation = conv_manager.load_conversation(kwargs['conversation_id'])
    if not active_conversation:
      click.echo(f"Error: Conversation {kwargs['conversation_id']} not found.")
      sys.exit(1)
    logger.info(f"Loaded conversation: {active_conversation.id}")

  # Continue most recent conversation if requested
  elif kwargs['continue_conv'] and not kwargs['new_conversation']:
    active_conversation = conv_manager.get_most_recent_conversation()
    if not active_conversation:
      click.echo("No previous conversations found to continue.")
      logger.info("No previous conversations found to continue, creating new conversation.")
    else:
      logger.info(f"Continuing conversation: {active_conversation.id}")

  # Create a new conversation if needed
  if (active_conversation is None) or kwargs['new_conversation']:
    # Get system prompt either from template or defaults
    system_prompt = kwargs.get('systemprompt')
    if system_prompt:
      # Apply any spacetime placeholders
      system_prompt = spacetime_placeholders(system_prompt)

    # Create new conversation with optional title and model metadata
    conversation_metadata = {
      'model': kwargs.get('model'),
      'temperature': kwargs.get('temperature'),
      'max_tokens': kwargs.get('max_tokens'),
      'template': kwargs.get('template')
    }

    active_conversation = conv_manager.new_conversation(
      system_prompt=system_prompt,
      title=kwargs.get('title'),
      metadata=conversation_metadata
    )
    logger.info(f"Created new conversation: {active_conversation.id}")

  return active_conversation


def process_template_and_defaults(kwargs: Dict[str, Any], config: Dict[str, Any], template_path: str) -> None:
  """
  Process template parameters and apply default configuration values.
  
  This function first applies any specified template parameters to kwargs,
  then fills in any remaining None values with defaults from config.
  Template parameters take precedence over command-line defaults.
  
  Args:
    kwargs: Command-line arguments dictionary (modified in place)
    config: Configuration dictionary containing default values
    template_path: File system path to the Agents.json template file
    
  Raises:
    ConfigurationError: If template file cannot be loaded or parsed
    TemplateError: If specified template name is not found
    SystemExit: On template errors (exits with code 1)
  """
  defaults = config['defaults']

  # Process template if specified
  if kwargs['template'] or defaults.get('template'):
    template_name = kwargs['template'] or defaults.get('template')
    try:
      key, template = get_template(template_name, template_path)
      kwargs['template'] = key
      for k, v in template.items():
        if k in kwargs and (kwargs[k] is None or kwargs[k] == defaults.get(k)):
          kwargs[k] = v
    except (ConfigurationError, TemplateError) as e:
      click.echo(f"Template error: {e}", err=True)
      sys.exit(1)

  # Set default values for any remaining None parameters
  for key, default_value in defaults.items():
    if kwargs.get(key) is None:
      kwargs[key] = default_value


def setup_model_and_clients(kwargs: Dict[str, Any], models_json_path: str) -> tuple:
  """
  Resolve model name to canonical form and retrieve model parameters.
  
  Converts model aliases (like 'gpt4' or 'sonnet') to their canonical names
  (like 'gpt-4-turbo' or 'claude-3-5-sonnet-latest') and retrieves the
  corresponding model configuration including API requirements and limits.
  
  Args:
    kwargs: Command-line arguments containing model name
    models_json_path: File system path to Models.json configuration file
    
  Returns:
    tuple: (canonical_model_name, model_parameters_dict)
      - canonical_model_name (str): Full model name for API calls
      - model_parameters_dict (Dict): Model config including context limits, API key type
    
  Raises:
    ConfigurationError: If Models.json cannot be loaded or parsed
    ModelError: If specified model name is not found in Models.json
    SystemExit: On any model-related errors (exits with code 1)
  """
  try:
    canonical_model, model_parameters = get_canonical_model(kwargs['model'], models_json_path)
    return canonical_model, model_parameters
  except ConfigurationError as e:
    click.echo(f"Configuration error: {e}", err=True)
    sys.exit(1)
  except ModelError as e:
    click.echo(f"Model error: {e}", err=True)
    sys.exit(1)


def process_reference_and_knowledge(kwargs: Dict[str, Any], paths: Dict[str, str], api_keys: Dict[str, str], knowledgebase_query: str) -> tuple:
  """
  Process reference files and knowledge base content for inclusion in queries.
  
  This function handles two types of contextual information:
  1. Reference files: Text files specified via -r/--reference flag
  2. Knowledge base: Vector database content queried via -k/--knowledgebase flag
  
  Both are formatted as XML-wrapped strings for safe inclusion in LLM queries.
  
  Args:
    kwargs: Command-line arguments containing reference and knowledgebase options
    paths: Dictionary of file paths including customkb_executable and vectordbs_path
    api_keys: API keys dictionary for potential KB authentication
    knowledgebase_query: Query string to send to the knowledge base
    
  Returns:
    tuple: (reference_string, knowledgebase_string)
      - reference_string (str): XML-wrapped content of reference files
      - knowledgebase_string (str): XML-wrapped knowledge base query results
    
  Raises:
    ReferenceError: If reference files cannot be read or processed
    KnowledgeBaseError: If knowledge base cannot be queried
    SystemExit: On file not found or unexpected errors (exits with code 1)
  """
  # Process references
  try:
    reference_string = get_reference_string(kwargs['reference'])
  except ReferenceError as e:
    click.echo(f"Reference error: {e}", err=True)
    sys.exit(1)
  except Exception as e:
    click.echo(f"Unexpected error processing references: {str(e)}", err=True)
    sys.exit(1)

  # Process knowledgebase
  knowledgebase_string = ''
  if kwargs['knowledgebase']:
    try:
      # Fix path handling for okusi knowledgebases by normalizing path format
      kb_path = kwargs['knowledgebase']
      if '/' in kb_path and not kb_path.endswith('.cfg'):
        # Handle format like "okusi/okusiassociates" by converting to full path
        kb_parts = kb_path.split('/')
        if len(kb_parts) == 2:
          kb_path = os.path.join(paths['vectordbs_path'], kb_parts[0], f"{kb_parts[1]}.cfg")

      # Check if we should bypass knowledgebase errors and continue anyway
      bypass_kb_errors = os.environ.get('DV2_BYPASS_KB_ERRORS', 'false').lower() == 'true'

      try:
        knowledgebase_string = get_knowledgebase_string(
          kb_path,
          knowledgebase_query,
          paths['customkb_executable'],
          paths['vectordbs_path'],
          api_keys
        )
      except KnowledgeBaseError as e:
        error_msg = f"Knowledge base error: {e}"
        if bypass_kb_errors:
          click.echo(f"Warning: {error_msg} (continuing without knowledgebase)", err=True)
          knowledgebase_string = f"<knowledgebase>\n# Error querying knowledgebase (continuing without it)\n</knowledgebase>\n\n"
        else:
          click.echo(error_msg, err=True)
          sys.exit(1)
      except Exception as e:
        error_msg = f"Unexpected error querying knowledgebase: {str(e)}"
        if bypass_kb_errors:
          click.echo(f"Warning: {error_msg} (continuing without knowledgebase)", err=True)
          knowledgebase_string = f"<knowledgebase>\n# Error querying knowledgebase (continuing without it)\n</knowledgebase>\n\n"
        else:
          click.echo(error_msg, err=True)
          sys.exit(1)
    except FileNotFoundError as e:
      click.echo(f"Error: {str(e)}", err=True)
      sys.exit(1)
    except Exception as e:
      click.echo(f"Unexpected error with knowledgebase: {str(e)}", err=True)
      sys.exit(1)

  return reference_string, knowledgebase_string


# MAIN COMMAND LINE INTERFACE ============================================================
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument('query_text', nargs=-1, required=False)
@click.option('-V', '--version', is_flag=True,
              callback=lambda ctx, param, value: click.echo(f"dejavu2-cli v{VERSION}") or ctx.exit() if value else None,
              help='Show version and exit', is_eager=True)

@click.option('-T', '--template', default=None,
        help='The template name to initialize arguments from (eg, "Helpful_AI")')
@click.option('-m', '--model', default=None,
        help='The LLM model to use (eg, "gpt-4")')
@click.option('-s', '--systemprompt', default=None,
        help='The system role for the AI assistant (eg, "You are a helpful assistant.")')
@click.option('-t', '--temperature', type=float, default=None,
        help='The sampling temperature for the LLM (eg, 0.7)')
@click.option('-M', '--max-tokens', type=int, default=None,
        help='The maximum number of tokens for the LLM (eg, 1000)')

@click.option('-r', '--reference', default=None,
        help='A comma-delimited list of text files for inclusion as context before the query')
@click.option('-k', '--knowledgebase', default=None,
        help='The knowledge base for the query (eg, "my_knowledge_base")')
@click.option('-Q', '--knowledgebase-query', default=None,
        help='Query to be sent to the knowledge base instead of the command-line query')

@click.option('-S', '--status', is_flag=True, default=False,
        help='Display the state of all arguments and exit')
@click.option('-P', '--print-systemprompt', is_flag=True, default=False,
        help='Print the full system prompt when using --status')

@click.option('-a', '--list-models', is_flag=True, default=False,
        help='List all available models from Models.json')
@click.option('-A', '--list-models-details', is_flag=True, default=False,
        help='List all available models from Models.json, and display all elements')
@click.option('-l', '--list-template', default=None,
        help='List all templates, or a specific template (eg, "all" or "Helpful_AI")')
@click.option('-L', '--list-template-names', is_flag=True, default=False,
        help='List the templates, without the systemprompt')
@click.option('-K', '--list-knowledge-bases', is_flag=True, default=False,
        help='List all available knowledge bases')

@click.option('-E', '--edit-templates', is_flag=True, default=False,
        help='Edit Agents.json file')
@click.option('-D', '--edit-defaults', is_flag=True, default=False,
        help='Edit defaults.yaml file')
@click.option('-d', '--edit-models', is_flag=True, default=False,
        help='Edit Models.json')

@click.option('-p', '--project-name', default=None,
        help='The project name for recording conversations (eg, -p "bali_market")')
@click.option('-o', '--output-dir', default=None,
        help='Directory to output results to (eg, "/tmp/myfiles")')
@click.option('-g', '--message', type=(str, str), multiple=True,
        help='Add message pairs in the form: -g role "message" (eg, -g user "hello" -g assistant "hi")')

# Conversation history options
@click.option('-c', '--continue', 'continue_conv', is_flag=True, default=False,
        help='Continue the most recent conversation')
@click.option('--conversation', '-C', 'conversation_id', type=str,
        help='Load a specific conversation by ID')
@click.option('--list-conversations', '-x', is_flag=True, default=False,
        help='List all saved conversations')
@click.option('--delete-conversation', '-X', type=str,
        help='Delete a specific conversation by ID')
@click.option('--new-conversation', '-n', is_flag=True, default=False,
        help='Start a new conversation even when continuing would be possible')
@click.option('--title', '-i', type=str,
        help='Set a title for a new conversation')
@click.option('--export-conversation', '-e', type=str,
        help='Export a conversation to markdown (specify ID or "current")')
@click.option('--export-path', '-f', type=str,
        help='Path to save the exported conversation markdown file')
@click.option('--stdout', '-O', is_flag=True, default=False,
        help='Output the exported conversation to stdout instead of a file')
@click.option('--list-messages', '-W', type=str, metavar='CONVERSATION_ID',
        help='List all messages in a conversation with their indices and content previews')
@click.option('--remove-message', nargs=2, type=(str, int), metavar=('CONVERSATION_ID', 'MESSAGE_INDEX'),
        help='Remove a single message from a conversation (use --list-messages first to find indices)')
@click.option('--remove-pair', nargs=2, type=(str, int), metavar=('CONVERSATION_ID', 'USER_MESSAGE_INDEX'),
        help='Remove a user-assistant message pair (index must point to a user message followed by an assistant message)')

# Logging options
@click.option('-v', '--verbose', is_flag=True, default=False,
        help='Enable verbose (debug level) logging')
@click.option('--log-file', type=str,
        help='Path to a log file where all logs will be written')
@click.option('-q', '--quiet', is_flag=True, default=True,
        help='Suppress log messages except for errors')
# Note: verbose and quiet can't both be True - verbose takes precedence

def main(**kwargs: Any) -> None:
    """
    Main entry point for the dejavu2-cli program.

    Processes command-line arguments, handles utility commands (like listing templates
    or editing configuration files), and executes LLM queries with the specified parameters.

    Features include:
    - Querying various LLM providers (OpenAI, Anthropic, local models)
    - Including reference files and knowledge base content with queries
    - Using templates for consistent parameters
    - Maintaining conversation history across multiple interactions
    - Saving and loading conversations

    Args:
        **kwargs: Command-line arguments parsed by Click
    """
    # Override the program name for help display
    ctx = click.get_current_context()
    ctx.info_name = 'dejavu2-cli'
    # Setup application (logging, config, paths)
    logger, config, paths = setup_application(kwargs)
    
    # Initialize conversation manager
    conv_manager = ConversationManager()

    # Handle utility commands first
    if handle_utility_commands(kwargs, paths):
        return

    # Handle conversation listing
    if kwargs['list_conversations']:
        handle_conversation_listing(conv_manager)
        return

    # Handle conversation deletion
    if kwargs['delete_conversation']:
        handle_conversation_deletion(conv_manager, kwargs['delete_conversation'])
        return

    # Handle message operations
    if handle_message_operations(kwargs, conv_manager):
        return

    # Handle conversation export
    if kwargs['export_conversation']:
        handle_conversation_export(kwargs, conv_manager)
        return

    # Prepare for query execution
    query_context = prepare_query_execution(kwargs, config, paths, conv_manager)
    
    # Handle status display
    if kwargs['status']:
        display_status(kwargs, query_context['query_texts'], config, query_context['model_parameters'],
                      kwargs.get('print_systemprompt', False), query_context['active_conversation'])
        return
    
    # Execute the queries
    execute_queries(query_context, conv_manager)


def execute_queries(query_context: Dict[str, Any], conv_manager: ConversationManager) -> None:
  """
  Execute the actual LLM queries and handle responses.
  
  Args:
    query_context: Dictionary containing all query context
    conv_manager: ConversationManager instance
  """
  kwargs = query_context['kwargs']
  query_result = ''
  prev_query_text = ''
  output_files = []
  output_order = 0

  for query_text in query_context['query_texts']:
    # If multiple queries, append the result of the previous query results
    if query_result:
      query_result = f"""

<ChainOfThought>
---User:

{prev_query_text.strip()}

---Assistant:

{query_result.strip()}

</ChainOfThought>

"""

    # Combine all parts of the query with proper XML escaping
    llm_queries_wrapper = ['<LLM_Queries>\n', '\n</LLM_Queries>\n']
    
    # Escape user input for XML safety
    safe_query_text = xml.sax.saxutils.escape(query_text) if query_text else ""
    safe_query_result = xml.sax.saxutils.escape(query_result) if query_result else ""
    
    full_query = f"{llm_queries_wrapper[0]}<Query>\n{query_context['reference_string']}\n{query_context['knowledgebase_string']}\n{safe_query_result}\n{safe_query_text}\n</Query>{llm_queries_wrapper[1]}\n"

    # Add current query to the conversation
    if query_context['active_conversation']:
      query_context['active_conversation'].add_message("user", query_text)

    # Execute the query
    try:
      query_result = query(
        query_context['clients'],
        full_query,
        systemprompt=kwargs['systemprompt'],
        messages=query_context['messages'],
        model=kwargs['model'],
        temperature=kwargs['temperature'],
        max_tokens=kwargs['max_tokens'],
        model_parameters=query_context['model_parameters'],
        api_keys=query_context['api_keys']
      )

      # Ensure query_result is a string
      if not isinstance(query_result, str):
        if hasattr(query_result, 'text'):
          query_result = query_result.text
        elif isinstance(query_result, (list, dict)):
          query_result = str(query_result)
        else:
          query_result = str(query_result)

      # Handle conversation response
      handle_conversation_response(query_context, conv_manager, query_result)

      # Display the response
      click.echo(query_result + '\n')

      # Handle file output
      handle_file_output(query_context, query_text, query_result, output_files, output_order)
      output_order += 1
      
    except Exception as e:
      click.echo(f"Error: {str(e)}", err=True)
      if query_context['active_conversation']:
        # Save that there was an error in the conversation
        query_context['active_conversation'].add_message("system", f"Error occurred: {str(e)}")
        conv_manager.save_conversation(query_context['active_conversation'])
      sys.exit(1)
    prev_query_text = query_text

  # Write combined file if multiple outputs
  write_combined_output_file(query_context, output_files)


def handle_conversation_response(query_context: Dict[str, Any], conv_manager: ConversationManager, query_result: str) -> None:
  """
  Process and save LLM response to the active conversation.
  
  This function adds the assistant's response to the conversation history,
  generates a title for new conversations if needed, and saves the updated
  conversation to persistent storage.
  
  Args:
    query_context: Dictionary containing query execution context including
                  active_conversation and other execution parameters
    conv_manager: ConversationManager instance for saving conversations
    query_result: The assistant's response text from the LLM
    
  Side Effects:
    - Adds assistant message to active conversation
    - Generates conversation title for new conversations
    - Saves conversation to persistent storage
    - Logs conversation save events
  """
  active_conversation = query_context['active_conversation']
  kwargs = query_context['kwargs']
  
  if active_conversation:
    active_conversation.add_message("assistant", query_result)

    # Update metadata with the latest parameters
    active_conversation.metadata.update({
      'model': kwargs.get('model'),
      'temperature': kwargs.get('temperature'),
      'max_tokens': kwargs.get('max_tokens'),
      'template': kwargs.get('template')
    })

    # Save after each message to prevent data loss
    conv_manager.save_conversation(active_conversation)

    # Generate a title if this is a new conversation with default title
    if (not active_conversation.title or active_conversation.title == 'Untitled Conversation') and len(active_conversation.messages) >= 3:
      # Simple title generation query function
      def simple_title_query(prompt):
        try:
          result = query(
            query_context['clients'],
            prompt,
            systemprompt="You are a helpful assistant that creates concise titles.",
            messages=[],
            model=kwargs['model'],
            temperature=0.7,
            max_tokens=20,
            model_parameters=query_context['model_parameters'],
            api_keys=query_context['api_keys']
          )
          # Ensure result is a string
          if not isinstance(result, str):
            if hasattr(result, 'text'):
              result = result.text
            elif isinstance(result, (list, dict)):
              result = str(result)
            else:
              result = str(result)
          return result
        except Exception:
          return "Untitled Conversation"

      title = conv_manager.suggest_title_from_content(
        active_conversation,
        simple_title_query
      )
      if title and title != "Untitled Conversation":
        active_conversation.title = title
        conv_manager.save_conversation(active_conversation)
        logger.info(f"Generated conversation title: {title}")


def handle_file_output(query_context: Dict[str, Any], query_text: str, query_result: str, output_files: List[str], output_order: int) -> None:
  """
  Handle writing query and response to output files.
  
  Args:
    query_context: Dictionary containing query context
    query_text: The user query
    query_result: The LLM response
    output_files: List of output file paths
    output_order: Current output order number
  """
  if query_context['output_dir']:
    safe_query = "".join(c for c in query_text[:100] if c.isalnum() or c in (' ', '_')).rstrip()
    safe_query = post_slug(safe_query, '-', False, 60)
    filename = os.path.join(query_context['output_dir'],
      f'dv2_{query_context["project_name"]}_{int(time.time())}_{output_order + 1}_{safe_query}.txt')

    with open(filename, 'w', encoding='utf-8') as file:
      file.write(f"---User:\n\n{query_text.strip()}\n\n")

    with open(filename, 'a', encoding='utf-8') as f:
      f.write(f"---Assistant:\n\n{query_result.strip()}\n\n")

    output_files.append(filename)


def write_combined_output_file(query_context: Dict[str, Any], output_files: List[str]) -> None:
  """
  Write combined output file if multiple queries were processed.
  
  Args:
    query_context: Dictionary containing query context
    output_files: List of output file paths
  """
  if len(output_files) > 1:
    filename_cot = os.path.join(query_context['output_dir'], f'dv2_{query_context["project_name"]}_{int(time.time())}_0_.txt')
    # Open the combined file in write mode
    with open(filename_cot, 'w', encoding='utf-8') as cot_file:
      for filename in output_files:
        # Open each output file in read mode
        with open(filename, 'r', encoding='utf-8') as file:
          # Read the entire content of the current file
          contents = file.read()
        # Append the content to the combined file with two newlines for separation
        cot_file.write(contents + '\n\n')

# Make the module importable for testing
if __name__ == '__main__':
    main()

#fin
