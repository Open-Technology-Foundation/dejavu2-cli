#!/bin/bash
# Bash completion for dejavu2-cli
# Installation:
#   1. Source this file: source dejavu2-cli-completion.bash
#   2. Or add to ~/.bashrc: echo "source /path/to/dejavu2-cli-completion.bash" >> ~/.bashrc
#   3. For system-wide: sudo cp dejavu2-cli-completion.bash /etc/bash_completion.d/

_dejavu2_cli_completions() {
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

  # Options that take arguments
  local arg_options="-T --template -m --model -s --systemprompt -t --temperature \
    -M --max-tokens -r --reference -k --knowledgebase -Q --knowledgebase-query \
    -l --list-template -p --project-name -o --output-dir -C --conversation \
    -X --delete-conversation -i --title -e --export-conversation -f --export-path \
    -W --list-messages --log-file"

  # Helper function to get dynamic completions
  _get_models() {
    if [[ -f "$script_dir/Models.json" ]]; then
      python3 -c "
import json
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
    pass
" 2>/dev/null || echo ""
    fi
  }

  _get_templates() {
    if [[ -f "$script_dir/Agents.json" ]]; then
      python3 -c "
import json
try:
    with open('$script_dir/Agents.json', 'r') as f:
        data = json.load(f)
        if isinstance(data, dict):
            print(' '.join(sorted(data.keys())))
except:
    pass
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
      # List directories and .cfg files
      find "$kb_dir" -maxdepth 2 \( -type d -o -name "*.cfg" \) 2>/dev/null | \
        grep -v "^$kb_dir$" | \
        sed "s|$kb_dir/||" | \
        sed 's/\.cfg$//' | \
        sort -u 2>/dev/null || echo ""
    fi
  }

  # Handle options with arguments
  case "$prev" in
    -T|--template)
      COMPREPLY=($(compgen -W "$(_get_templates)" -- "$cur"))
      return 0
      ;;
    -m|--model)
      COMPREPLY=($(compgen -W "$(_get_models)" -- "$cur"))
      return 0
      ;;
    -s|--systemprompt)
      # No specific completion for system prompt
      return 0
      ;;
    -t|--temperature)
      COMPREPLY=($(compgen -W "0.0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0" -- "$cur"))
      return 0
      ;;
    -M|--max-tokens)
      COMPREPLY=($(compgen -W "100 500 1000 2000 4000 8000 16000 32000" -- "$cur"))
      return 0
      ;;
    -r|--reference)
      # Complete with files
      COMPREPLY=($(compgen -f -- "$cur"))
      return 0
      ;;
    -k|--knowledgebase)
      COMPREPLY=($(compgen -W "$(_get_knowledge_bases)" -- "$cur"))
      return 0
      ;;
    -Q|--knowledgebase-query)
      # No specific completion for KB query
      return 0
      ;;
    -l|--list-template)
      local templates="all $(_get_templates)"
      COMPREPLY=($(compgen -W "$templates" -- "$cur"))
      return 0
      ;;
    -p|--project-name)
      # No specific completion for project name
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
      fi
      return 0
      ;;
    -C|--conversation|-X|--delete-conversation|-W|--list-messages)
      COMPREPLY=($(compgen -W "$(_get_conversations)" -- "$cur"))
      return 0
      ;;
    -i|--title)
      # No specific completion for title
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
      # Add .md if completing a directory or no extension
      if [[ -d "$cur" ]] || [[ "$cur" != *.* ]]; then
        COMPREPLY+=("${cur}.md")
      fi
      return 0
      ;;
    --log-file)
      COMPREPLY=($(compgen -f -- "$cur"))
      return 0
      ;;
    --remove-message|--remove-pair)
      # These need conversation ID first
      if [[ "${words[cword-2]}" == "--remove-message" || "${words[cword-2]}" == "--remove-pair" ]]; then
        # Second argument is message index - suggest some common indices
        COMPREPLY=($(compgen -W "0 1 2 3 4 5 6 7 8 9 10" -- "$cur"))
      else
        # First argument is conversation ID
        COMPREPLY=($(compgen -W "$(_get_conversations)" -- "$cur"))
      fi
      return 0
      ;;
  esac

  # If current word starts with -, complete with options
  if [[ "$cur" == -* ]]; then
    COMPREPLY=($(compgen -W "$all_options" -- "$cur"))
    return 0
  fi

  # Check if we're in a position where we need to complete a second argument
  # for --remove-message or --remove-pair
  if [[ $cword -gt 2 ]]; then
    local two_prev="${words[cword-2]}"
    if [[ "$two_prev" == "--remove-message" || "$two_prev" == "--remove-pair" ]]; then
      # We're completing the message index
      COMPREPLY=($(compgen -W "0 1 2 3 4 5 6 7 8 9 10" -- "$cur"))
      return 0
    fi
  fi

  # Default: complete with files for query text
  COMPREPLY=($(compgen -f -- "$cur"))
}

# Register completions for all possible command names
complete -F _dejavu2_cli_completions dejavu2-cli
complete -F _dejavu2_cli_completions ./dejavu2-cli
complete -F _dejavu2_cli_completions dv2
complete -F _dejavu2_cli_completions ./dv2
complete -F _dejavu2_cli_completions dejavu2
complete -F _dejavu2_cli_completions ./dejavu2
complete -F _dejavu2_cli_completions dv2c
complete -F _dejavu2_cli_completions ./dv2c