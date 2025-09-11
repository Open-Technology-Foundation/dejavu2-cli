#!/bin/bash
# Advanced Bash completion for dejavu2-cli with descriptions
# Installation:
#   1. Source this file: source dejavu2-cli-completion-advanced.bash
#   2. Or add to ~/.bashrc: echo "source /path/to/dejavu2-cli-completion-advanced.bash" >> ~/.bashrc
#   3. For system-wide: sudo cp dejavu2-cli-completion-advanced.bash /etc/bash_completion.d/

_dejavu2_cli_completions_advanced() {
  local cur prev words cword
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  words=("${COMP_WORDS[@]}")
  cword=$COMP_CWORD

  # Get the command name (could be dejavu2-cli, ./dejavu2-cli, dv2, or ./dv2)
  local cmd="${words[0]}"
  
  # Path to the dejavu2-cli directory
  local script_dir
  if [[ "$cmd" == "./"* ]]; then
    script_dir="$(dirname "$(readlink -f "$cmd")")"
  else
    script_dir="$(dirname "$(which "$cmd" 2>/dev/null || echo "/ai/scripts/dejavu2-cli")")"
  fi

  # Option descriptions (for help display)
  declare -A option_desc=(
    ["-h"]="Show help and exit"
    ["--help"]="Show help and exit"
    ["-V"]="Show version and exit"
    ["--version"]="Show version and exit"
    ["-T"]="Template name to initialize arguments"
    ["--template"]="Template name to initialize arguments"
    ["-m"]="LLM model to use"
    ["--model"]="LLM model to use"
    ["-s"]="System role for the AI assistant"
    ["--systemprompt"]="System role for the AI assistant"
    ["-t"]="Sampling temperature for the LLM (0.0-1.0)"
    ["--temperature"]="Sampling temperature for the LLM (0.0-1.0)"
    ["-M"]="Maximum number of tokens for the LLM"
    ["--max-tokens"]="Maximum number of tokens for the LLM"
    ["-r"]="Comma-delimited list of reference files"
    ["--reference"]="Comma-delimited list of reference files"
    ["-k"]="Knowledgebase for the query"
    ["--knowledgebase"]="Knowledgebase for the query"
    ["-Q"]="Query to send to the knowledgebase"
    ["--knowledgebase-query"]="Query to send to the knowledgebase"
    ["-S"]="Display the state of all arguments and exit"
    ["--status"]="Display the state of all arguments and exit"
    ["-P"]="Print full system prompt with --status"
    ["--print-systemprompt"]="Print full system prompt with --status"
    ["-a"]="List all available models"
    ["--list-models"]="List all available models"
    ["-A"]="List models with all details"
    ["--list-models-details"]="List models with all details"
    ["-l"]="List templates (all or specific)"
    ["--list-template"]="List templates (all or specific)"
    ["-L"]="List template names only"
    ["--list-template-names"]="List template names only"
    ["-K"]="List all available knowledgebases"
    ["--list-knowledge-bases"]="List all available knowledgebases"
    ["-E"]="Edit Agents.json file"
    ["--edit-templates"]="Edit Agents.json file"
    ["-D"]="Edit defaults.yaml file"
    ["--edit-defaults"]="Edit defaults.yaml file"
    ["-d"]="Edit Models.json file"
    ["--edit-models"]="Edit Models.json file"
    ["-p"]="Project name for recording conversations"
    ["--project-name"]="Project name for recording conversations"
    ["-o"]="Directory to output results"
    ["--output-dir"]="Directory to output results"
    ["-g"]="Add message pairs: -g role \"message\""
    ["--message"]="Add message pairs: -g role \"message\""
    ["-c"]="Continue the most recent conversation"
    ["--continue"]="Continue the most recent conversation"
    ["-C"]="Load a specific conversation by ID"
    ["--conversation"]="Load a specific conversation by ID"
    ["-x"]="List all saved conversations"
    ["--list-conversations"]="List all saved conversations"
    ["-X"]="Delete a specific conversation by ID"
    ["--delete-conversation"]="Delete a specific conversation by ID"
    ["-n"]="Start a new conversation"
    ["--new-conversation"]="Start a new conversation"
    ["-i"]="Set a title for a new conversation"
    ["--title"]="Set a title for a new conversation"
    ["-e"]="Export conversation to markdown"
    ["--export-conversation"]="Export conversation to markdown"
    ["-f"]="Path to save exported conversation"
    ["--export-path"]="Path to save exported conversation"
    ["-O"]="Output exported conversation to stdout"
    ["--stdout"]="Output exported conversation to stdout"
    ["-W"]="List all messages in a conversation"
    ["--list-messages"]="List all messages in a conversation"
    ["--remove-message"]="Remove a single message from conversation"
    ["--remove-pair"]="Remove a user-assistant message pair"
    ["-v"]="Enable verbose (debug) logging"
    ["--verbose"]="Enable verbose (debug) logging"
    ["--log-file"]="Path to log file"
    ["-q"]="Suppress log messages except errors"
    ["--quiet"]="Suppress log messages except errors"
  )

  # All options
  local all_options="-h --help -V --version -T --template -m --model -s --systemprompt \
    -t --temperature -M --max-tokens -r --reference -k --knowledgebase \
    -Q --knowledgebase-query -S --status -P --print-systemprompt -a --list-models \
    -A --list-models-details -l --list-template -L --list-template-names \
    -K --list-knowledge-bases -E --edit-templates -D --edit-defaults -d --edit-models \
    -p --project-name -o --output-dir -g --message -c --continue -C --conversation \
    -x --list-conversations -X --delete-conversation -n --new-conversation -i --title \
    -e --export-conversation -f --export-path -O --stdout -W --list-messages \
    --remove-message --remove-pair -v --verbose --log-file -q --quiet"

  # Helper function to check if an option was already used
  _option_used() {
    local opt="$1"
    local i
    for ((i=1; i<cword; i++)); do
      if [[ "${words[i]}" == "$opt" ]]; then
        return 0
      fi
    done
    return 1
  }

  # Helper function to get unused options
  _get_unused_options() {
    local opts=""
    for opt in $all_options; do
      if ! _option_used "$opt"; then
        # Skip short form if long form was used and vice versa
        case "$opt" in
          -h) _option_used "--help" || opts="$opts $opt" ;;
          --help) _option_used "-h" || opts="$opts $opt" ;;
          -V) _option_used "--version" || opts="$opts $opt" ;;
          --version) _option_used "-V" || opts="$opts $opt" ;;
          -T) _option_used "--template" || opts="$opts $opt" ;;
          --template) _option_used "-T" || opts="$opts $opt" ;;
          -m) _option_used "--model" || opts="$opts $opt" ;;
          --model) _option_used "-m" || opts="$opts $opt" ;;
          -s) _option_used "--systemprompt" || opts="$opts $opt" ;;
          --systemprompt) _option_used "-s" || opts="$opts $opt" ;;
          -t) _option_used "--temperature" || opts="$opts $opt" ;;
          --temperature) _option_used "-t" || opts="$opts $opt" ;;
          -M) _option_used "--max-tokens" || opts="$opts $opt" ;;
          --max-tokens) _option_used "-M" || opts="$opts $opt" ;;
          -r) _option_used "--reference" || opts="$opts $opt" ;;
          --reference) _option_used "-r" || opts="$opts $opt" ;;
          -k) _option_used "--knowledgebase" || opts="$opts $opt" ;;
          --knowledgebase) _option_used "-k" || opts="$opts $opt" ;;
          -Q) _option_used "--knowledgebase-query" || opts="$opts $opt" ;;
          --knowledgebase-query) _option_used "-Q" || opts="$opts $opt" ;;
          -C) _option_used "--conversation" || opts="$opts $opt" ;;
          --conversation) _option_used "-C" || opts="$opts $opt" ;;
          -X) _option_used "--delete-conversation" || opts="$opts $opt" ;;
          --delete-conversation) _option_used "-X" || opts="$opts $opt" ;;
          -i) _option_used "--title" || opts="$opts $opt" ;;
          --title) _option_used "-i" || opts="$opts $opt" ;;
          -e) _option_used "--export-conversation" || opts="$opts $opt" ;;
          --export-conversation) _option_used "-e" || opts="$opts $opt" ;;
          -f) _option_used "--export-path" || opts="$opts $opt" ;;
          --export-path) _option_used "-f" || opts="$opts $opt" ;;
          -W) _option_used "--list-messages" || opts="$opts $opt" ;;
          --list-messages) _option_used "-W" || opts="$opts $opt" ;;
          *) opts="$opts $opt" ;;
        esac
      fi
    done
    echo "$opts"
  }

  # Helper functions for dynamic completions with caching
  _get_models() {
    if [[ -f "$script_dir/Models.json" ]]; then
      python3 -c "
import json, sys
try:
    with open('$script_dir/Models.json', 'r') as f:
        data = json.load(f)
        models = []
        for model in data.get('models', []):
            # Add canonical name
            if 'model' in model:
                models.append(model['model'])
            # Add aliases
            for alias in model.get('aliases', []):
                models.append(alias)
        print(' '.join(sorted(set(models))))
except:
    sys.exit(1)
" 2>/dev/null || echo ""
    fi
  }

  _get_templates() {
    if [[ -f "$script_dir/Agents.json" ]]; then
      python3 -c "
import json, sys
try:
    with open('$script_dir/Agents.json', 'r') as f:
        data = json.load(f)
        if isinstance(data, dict):
            print(' '.join(sorted(data.keys())))
except:
    sys.exit(1)
" 2>/dev/null || echo ""
    fi
  }

  _get_conversations() {
    local conv_dir="$HOME/.config/dejavu2-cli/conversations"
    if [[ -d "$conv_dir" ]]; then
      find "$conv_dir" -name "*.json" -type f 2>/dev/null | \
        xargs -I {} basename {} .json 2>/dev/null | sort || echo ""
    fi
  }

  _get_knowledge_bases() {
    local kb_dir="/var/lib/vectordbs"
    if [[ -d "$kb_dir" ]]; then
      # List directories and .cfg files with special handling for subdirectories
      (
        cd "$kb_dir" 2>/dev/null || exit
        # Find all .cfg files and format them nicely
        find . -name "*.cfg" -type f 2>/dev/null | \
          sed 's|^\./||' | \
          sed 's|\.cfg$||' | \
          sort
        # Also list first-level directories that might contain KB configs
        find . -maxdepth 1 -type d ! -name "." 2>/dev/null | \
          sed 's|^\./||' | \
          sort
      ) 2>/dev/null || echo ""
    fi
  }

  # Special handling for multi-part options
  case "$prev" in
    -T|--template)
      local templates=$(_get_templates)
      if [[ -n "$templates" ]]; then
        COMPREPLY=($(compgen -W "$templates" -- "$cur"))
      fi
      return 0
      ;;
    -m|--model)
      local models=$(_get_models)
      if [[ -n "$models" ]]; then
        COMPREPLY=($(compgen -W "$models" -- "$cur"))
      else
        # Fallback to common models if Models.json not available
        COMPREPLY=($(compgen -W "gpt-4 gpt-3.5-turbo claude-3-opus claude-3-sonnet claude-3-haiku" -- "$cur"))
      fi
      return 0
      ;;
    -s|--systemprompt)
      # Suggest some common system prompts
      if [[ -z "$cur" ]]; then
        COMPREPLY=("\"You are a helpful AI assistant.\"" "\"You are an expert programmer.\"" "\"You are a creative writer.\"")
      fi
      return 0
      ;;
    -t|--temperature)
      COMPREPLY=($(compgen -W "0.0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0" -- "$cur"))
      return 0
      ;;
    -M|--max-tokens)
      COMPREPLY=($(compgen -W "100 256 512 1000 1024 2000 2048 4000 4096 8000 8192 16000 32000" -- "$cur"))
      return 0
      ;;
    -r|--reference)
      # Complete with text files, preferring common extensions
      local files=$(compgen -f -- "$cur")
      local text_files=""
      for f in $files; do
        if [[ -f "$f" ]] && [[ "$f" =~ \.(txt|md|py|js|java|c|cpp|h|hpp|sh|yaml|yml|json|xml|html|css)$ ]]; then
          text_files="$text_files $f"
        elif [[ -d "$f" ]]; then
          text_files="$text_files $f/"
        fi
      done
      COMPREPLY=($(compgen -W "$text_files" -- "$cur"))
      [[ ${#COMPREPLY[@]} -eq 0 ]] && COMPREPLY=($(compgen -f -- "$cur"))
      return 0
      ;;
    -k|--knowledgebase)
      local kbs=$(_get_knowledge_bases)
      if [[ -n "$kbs" ]]; then
        COMPREPLY=($(compgen -W "$kbs" -- "$cur"))
      fi
      return 0
      ;;
    -Q|--knowledgebase-query)
      # No specific completion, but could suggest quotes
      if [[ -z "$cur" ]]; then
        COMPREPLY=("\"\"")
      fi
      return 0
      ;;
    -l|--list-template)
      local templates="all $(_get_templates)"
      COMPREPLY=($(compgen -W "$templates" -- "$cur"))
      return 0
      ;;
    -p|--project-name)
      # Suggest based on current directory name
      if [[ -z "$cur" ]]; then
        local dirname=$(basename "$PWD")
        COMPREPLY=("\"$dirname\"")
      fi
      return 0
      ;;
    -o|--output-dir)
      # Complete with directories
      COMPREPLY=($(compgen -d -- "$cur"))
      return 0
      ;;
    -g|--message)
      # First argument after -g should be role
      if [[ ${#words[@]} -gt 2 ]] && [[ "${words[cword-2]}" == "-g" || "${words[cword-2]}" == "--message" ]]; then
        COMPREPLY=($(compgen -W "user assistant system" -- "$cur"))
      else
        # Second argument is the message content - suggest quotes
        if [[ -z "$cur" ]]; then
          COMPREPLY=("\"\"")
        fi
      fi
      return 0
      ;;
    -C|--conversation|-X|--delete-conversation|-W|--list-messages)
      local conversations=$(_get_conversations)
      if [[ -n "$conversations" ]]; then
        COMPREPLY=($(compgen -W "$conversations" -- "$cur"))
      fi
      return 0
      ;;
    -i|--title)
      # Suggest quotes for title
      if [[ -z "$cur" ]]; then
        COMPREPLY=("\"\"")
      fi
      return 0
      ;;
    -e|--export-conversation)
      local conversations="current $(_get_conversations)"
      COMPREPLY=($(compgen -W "$conversations" -- "$cur"))
      return 0
      ;;
    -f|--export-path)
      # Complete with files, prefer .md extension
      COMPREPLY=($(compgen -f -- "$cur"))
      # Suggest .md extension if no extension present
      if [[ ! "$cur" =~ \. ]] && [[ ${#COMPREPLY[@]} -eq 0 || -d "${COMPREPLY[0]}" ]]; then
        local base="${cur##*/}"
        [[ -z "$base" ]] && base="conversation"
        COMPREPLY+=("${cur}${base}.md")
      fi
      return 0
      ;;
    --log-file)
      # Suggest log file names
      COMPREPLY=($(compgen -f -- "$cur"))
      if [[ -z "$cur" || "$cur" == */ ]]; then
        COMPREPLY+=("${cur}dejavu2-cli.log")
      fi
      return 0
      ;;
    --remove-message|--remove-pair)
      # These need conversation ID first
      if [[ "${words[cword-2]}" == "--remove-message" || "${words[cword-2]}" == "--remove-pair" ]]; then
        # Second argument is message index
        COMPREPLY=($(compgen -W "0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 20 25 30" -- "$cur"))
      else
        # First argument is conversation ID
        local conversations=$(_get_conversations)
        if [[ -n "$conversations" ]]; then
          COMPREPLY=($(compgen -W "$conversations" -- "$cur"))
        fi
      fi
      return 0
      ;;
  esac

  # Handle role completion for message pairs
  if [[ $cword -gt 2 ]] && [[ "${words[cword-2]}" == "-g" || "${words[cword-2]}" == "--message" ]]; then
    COMPREPLY=($(compgen -W "user assistant system" -- "$cur"))
    return 0
  fi

  # If current word starts with -, complete with unused options
  if [[ "$cur" == -* ]]; then
    local unused_opts=$(_get_unused_options)
    COMPREPLY=($(compgen -W "$unused_opts" -- "$cur"))
    return 0
  fi

  # Check if we're in a position where we need to complete a second argument
  # for --remove-message or --remove-pair
  if [[ $cword -gt 2 ]]; then
    local two_prev="${words[cword-2]}"
    if [[ "$two_prev" == "--remove-message" || "$two_prev" == "--remove-pair" ]]; then
      # We're completing the message index
      COMPREPLY=($(compgen -W "0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 20 25 30" -- "$cur"))
      return 0
    fi
  fi

  # Check if we should not complete files (after certain flags)
  local no_file_completion=false
  for ((i=1; i<cword; i++)); do
    case "${words[i]}" in
      -S|--status|-a|--list-models|-A|--list-models-details|-L|--list-template-names|\
      -K|--list-knowledge-bases|-E|--edit-templates|-D|--edit-defaults|-d|--edit-models|\
      -x|--list-conversations|-V|--version|-h|--help)
        no_file_completion=true
        break
        ;;
    esac
  done

  if [[ "$no_file_completion" == false ]]; then
    # Default: complete with files for query text
    COMPREPLY=($(compgen -f -- "$cur"))
  fi
}

# Enable extended pattern matching for better completion
shopt -s extglob

# Register completions for all possible command names
complete -F _dejavu2_cli_completions_advanced dejavu2-cli
complete -F _dejavu2_cli_completions_advanced ./dejavu2-cli
complete -F _dejavu2_cli_completions_advanced dv2
complete -F _dejavu2_cli_completions_advanced ./dv2
complete -F _dejavu2_cli_completions_advanced dejavu2
complete -F _dejavu2_cli_completions_advanced ./dejavu2
complete -F _dejavu2_cli_completions_advanced dv2c
complete -F _dejavu2_cli_completions_advanced ./dv2c

# Add help function for interactive use
dejavu2_cli_completion_help() {
  echo "Dejavu2-CLI Bash Completion Help"
  echo "================================"
  echo ""
  echo "This completion script provides intelligent tab completion for dejavu2-cli commands."
  echo ""
  echo "Features:"
  echo "  - Complete all command-line options"
  echo "  - Dynamic completion for models from Models.json"
  echo "  - Dynamic completion for templates from Agents.json"
  echo "  - Dynamic completion for saved conversations"
  echo "  - Dynamic completion for knowledgebases"
  echo "  - Context-aware completion (e.g., roles after -g/--message)"
  echo "  - File and directory completion where appropriate"
  echo "  - Prevents duplicate options from being suggested"
  echo ""
  echo "Installation:"
  echo "  1. Source this file: source $0"
  echo "  2. Add to ~/.bashrc for permanent use"
  echo "  3. Or copy to /etc/bash_completion.d/ for system-wide use"
  echo ""
  echo "Usage:"
  echo "  Type 'dejavu2-cli ' or 'dv2 ' and press TAB to see available options"
  echo "  Continue pressing TAB to cycle through completions"
  echo ""
}