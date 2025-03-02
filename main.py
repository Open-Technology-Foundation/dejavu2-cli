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
from conversations import ConversationManager, Conversation

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
@click.option('--conversation', 'conversation_id', type=str,
        help='Load a specific conversation by ID')
@click.option('--list-conversations', is_flag=True, default=False,
        help='List all saved conversations')
@click.option('--delete-conversation', type=str,
        help='Delete a specific conversation by ID')
@click.option('--new-conversation', is_flag=True, default=False,
        help='Start a new conversation even when continuing would be possible')
@click.option('--title', type=str,
        help='Set a title for a new conversation')

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
    
    # Set template path
    template_path = os.path.join(PRGDIR, config['paths']['template_path'])
    models_json_path = os.path.join(PRGDIR, 'Models.json')
    customkb_executable = config['paths']['customkb']
    vectordbs_path = config.get('vectordbs_path', '/var/lib/vectordbs')
    
    # Initialize conversation manager
    conv_manager = ConversationManager()
    
    # Handle special options first
    if kwargs['edit_templates']:
        edit_json_file(template_path)
        return

    if kwargs['edit_defaults']:
        edit_yaml_file(DEFAULT_CONFIG_PATH)
        return

    if kwargs['list_template']:
        list_templates(template_path, kwargs['list_template'])
        return

    if kwargs['list_template_names']:
        list_template_names(template_path)
        return

    if kwargs['list_models']:
        list_models(models_json_path, False)
        return
        
    if kwargs['list_models_details']:
        list_models(models_json_path, True)
        return
        
    if kwargs.get('edit_models'):
        edit_json_file(models_json_path)
        return

    if kwargs['list_knowledge_bases']:
        list_knowledge_bases(vectordbs_path)
        return
        
    # Handle conversation listing
    if kwargs['list_conversations']:
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
        return
    
    # Handle conversation deletion
    if kwargs['delete_conversation']:
        if conv_manager.delete_conversation(kwargs['delete_conversation']):
            click.echo(f"Conversation {kwargs['delete_conversation']} deleted.")
        else:
            click.echo(f"Conversation {kwargs['delete_conversation']} not found.")
        return

    if kwargs['output_dir']:
        output_dir = kwargs.get('output_dir')
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = ''

    # Give conversations a project name
    project_name = ''
    if kwargs['project_name']:
        project_name = post_slug(kwargs['project_name'], '-', False, 24)
    if not project_name:
        project_name = 'noproj'
        
    # Handle active conversation
    active_conversation = None
    
    # Load specific conversation if requested
    if kwargs['conversation_id']:
        active_conversation = conv_manager.load_conversation(kwargs['conversation_id'])
        if not active_conversation:
            click.echo(f"Error: Conversation {kwargs['conversation_id']} not found.")
            return
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

    # Load defaults
    defaults = config['defaults']

    # Process template if specified
    if kwargs['template'] or defaults.get('template'):
        template_name = kwargs['template'] or defaults.get('template')
        template_data = get_template(template_name, template_path)
        if template_data:
            key, template = template_data
            kwargs['template'] = key
            for k, v in template.items():
                if k in kwargs and (kwargs[k] is None or kwargs[k] == defaults.get(k)):
                    kwargs[k] = v
        else:
            click.echo(f"Template '{template_name}' not found.", err=True)
            sys.exit(1)

    # Get messages from command line and convert to list (may be tuple from click)
    messages = list(kwargs.get('message', []))

    # Set default values for any remaining None parameters
    for key, default_value in defaults.items():
        if kwargs.get(key) is None:
            kwargs[key] = default_value

    # Get model info and initialize clients
    canonical_model, model_parameters = get_canonical_model(kwargs['model'], models_json_path)
    if not canonical_model:
        click.echo(f"Model '{kwargs['model']}' not found", err=True)
        sys.exit(1)
        
    kwargs['model'] = canonical_model

    # Get API keys and initialize clients
    api_keys = get_api_keys()
    clients = initialize_clients(api_keys)
    
    # Validate API keys based on model
    api_key_type = model_parameters.get('apikey', '')
    if api_key_type and not api_keys.get(api_key_type, ''):
        model_parameters['api_key_valid'] = False
    else:
        model_parameters['api_key_valid'] = True

    # Handle either the long form or short form of print_systemprompt flag
    show_full_systemprompt = kwargs.get('print_systemprompt', False)
    
    if kwargs['status']:
        display_status(kwargs, query_texts, config, model_parameters, 
                      show_full_systemprompt, active_conversation)
        return
        
    # Add existing messages from conversation if they exist
    conversation_messages = []
    if active_conversation and active_conversation.messages:
        # Remove system message from the extracted messages
        conversation_messages = active_conversation.get_messages_for_llm(include_system=False)
        
        if conversation_messages:
            logger.debug(f"Using {len(conversation_messages)} messages from conversation history")
            # If we have conversation history, add it to messages list
            messages.extend(conversation_messages)

    # Process references
    try:
        reference_string = get_reference_string(kwargs['reference'])
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
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
                    kb_path = os.path.join(vectordbs_path, kb_parts[0], f"{kb_parts[1]}.cfg")
            
            # Check if we should bypass knowledgebase errors and continue anyway
            bypass_kb_errors = os.environ.get('DV2_BYPASS_KB_ERRORS', 'false').lower() == 'true'
            
            try:
                knowledgebase_string = get_knowledgebase_string(
                    kb_path, 
                    knowledgebase_query, 
                    customkb_executable, 
                    vectordbs_path, 
                    api_keys
                )
            except Exception as e:
                # Provide more helpful error message about API key issues
                if hasattr(e, 'stderr') and "invalid_api_key" in str(e.stderr):
                    error_msg = f"Error: Invalid OpenAI API key when querying knowledgebase. Please check your OPENAI_API_KEY environment variable."
                else:
                    error_msg = f"Error querying knowledgebase: {str(e)}"
                
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

    # Execute queries --------------------------------------------------------
    query_result = ''
    prev_query_text = ''
    output_files = []
    output_order = 0
    
    for query_text in query_texts:
        # if multiple queries, append the result of the previous query results
        if query_result:
            query_result = f"""

<ChainOfThought>
---User:

{prev_query_text.strip()}

---Assistant:

{query_result.strip()}

</ChainOfThought>

"""

        # Combine all parts of the query
        llm_queries_wrapper = ['<LLM_Queries>\n', '\n</LLM_Queries>\n']
        full_query = f"{llm_queries_wrapper[0]}<Query>\n{reference_string}\n{knowledgebase_string}\n{query_result}\n{query_text}\n</Query>{llm_queries_wrapper[1]}\n"
        
        # Add current query to the conversation
        if active_conversation:
            active_conversation.add_message("user", query_text)
        
        # Execute the query
        try:
            query_result = query(
                clients,
                full_query,
                systemprompt=kwargs['systemprompt'],
                messages=messages,
                model=kwargs['model'],
                temperature=kwargs['temperature'],
                max_tokens=kwargs['max_tokens'],
                model_parameters=model_parameters,
                api_keys=api_keys
            )
            
            # Add response to conversation
            if active_conversation:
                active_conversation.add_message("assistant", query_result)
                
                # Update metadata with the latest parameters
                # This ensures metadata stays current if parameters were changed mid-conversation
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
                                clients,
                                prompt,
                                systemprompt="You are a helpful assistant that creates concise titles.",
                                messages=[],
                                model=kwargs['model'],
                                temperature=0.7,
                                max_tokens=20,
                                model_parameters=model_parameters,
                                api_keys=api_keys
                            )
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
            
            # Display the response
            click.echo(query_result + '\n')
            
            if output_dir:
                output_order += 1
                safe_query = "".join(c for c in query_text[:100] if c.isalnum() or c in (' ', '_')).rstrip()
                safe_query = post_slug(safe_query, '-', False, 60)
                filename = os.path.join(output_dir,
                    f'dv2_{project_name}_{int(time.time())}_{output_order}_{safe_query}.txt')

                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(f"---User:\n\n{query_text.strip()}\n\n")

                with open(filename, 'a', encoding='utf-8') as f:
                    f.write(f"---Assistant:\n\n{query_result.strip()}\n\n")

                output_files.append(filename)
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            if active_conversation:
                # Save that there was an error in the conversation
                active_conversation.add_message("system", f"Error occurred: {str(e)}")
                conv_manager.save_conversation(active_conversation)
            sys.exit(1)
        prev_query_text = query_text

    # Write out all the files to one CoT conversation if multiple outputs
    if len(output_files) > 1:
        filename_cot = os.path.join(output_dir, f'dv2_{project_name}_{int(time.time())}_0_.txt')
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
