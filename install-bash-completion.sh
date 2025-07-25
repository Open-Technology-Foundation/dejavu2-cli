#!/bin/bash
# Installation script for dejavu2-cli bash completion

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPLETION_FILE="dejavu2-cli-completion.bash"
ADVANCED_COMPLETION_FILE="dejavu2-cli-completion-advanced.bash"

echo "Dejavu2-CLI Bash Completion Installer"
echo "====================================="
echo ""

# Check if running with sudo for system-wide installation
if [[ $EUID -eq 0 ]]; then
    echo "Running as root - will install system-wide"
    INSTALL_SYSTEM=true
else
    echo "Running as user - will install for current user only"
    INSTALL_SYSTEM=false
fi

# Let user choose between basic and advanced completion
echo ""
echo "Which completion version would you like to install?"
echo "1) Basic - Simple completions with dynamic model/template lookup"
echo "2) Advanced - Enhanced completions with smart context awareness"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        SOURCE_FILE="$SCRIPT_DIR/$COMPLETION_FILE"
        ;;
    2)
        SOURCE_FILE="$SCRIPT_DIR/$ADVANCED_COMPLETION_FILE"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

if [[ ! -f "$SOURCE_FILE" ]]; then
    echo "Error: Completion file not found: $SOURCE_FILE"
    exit 1
fi

if $INSTALL_SYSTEM; then
    # System-wide installation
    if [[ -d /etc/bash_completion.d ]]; then
        echo "Installing to /etc/bash_completion.d/..."
        cp "$SOURCE_FILE" /etc/bash_completion.d/dejavu2-cli
        echo "System-wide installation complete!"
        echo ""
        echo "The completion will be available in new shell sessions."
    else
        echo "Error: /etc/bash_completion.d/ not found"
        echo "Your system might not support bash-completion."
        exit 1
    fi
else
    # User installation
    BASHRC="$HOME/.bashrc"
    
    # Check if already installed
    if grep -q "dejavu2-cli.*completion" "$BASHRC" 2>/dev/null; then
        echo "Dejavu2-CLI completion appears to already be installed in $BASHRC"
        read -p "Do you want to reinstall? (y/N): " reinstall
        if [[ "$reinstall" != "y" && "$reinstall" != "Y" ]]; then
            echo "Installation cancelled."
            exit 0
        fi
        # Remove old installation
        sed -i '/# Dejavu2-CLI bash completion/,/dejavu2-cli.*completion.*\.bash/d' "$BASHRC"
    fi
    
    # Create local completion directory if it doesn't exist
    LOCAL_COMPLETION_DIR="$HOME/.local/share/bash-completion"
    mkdir -p "$LOCAL_COMPLETION_DIR"
    
    # Copy completion file
    cp "$SOURCE_FILE" "$LOCAL_COMPLETION_DIR/dejavu2-cli-completion.bash"
    
    # Add to .bashrc
    echo "" >> "$BASHRC"
    echo "# Dejavu2-CLI bash completion" >> "$BASHRC"
    echo "if [[ -f \"$LOCAL_COMPLETION_DIR/dejavu2-cli-completion.bash\" ]]; then" >> "$BASHRC"
    echo "    source \"$LOCAL_COMPLETION_DIR/dejavu2-cli-completion.bash\"" >> "$BASHRC"
    echo "fi" >> "$BASHRC"
    
    echo "User installation complete!"
    echo ""
    echo "Run 'source ~/.bashrc' or start a new shell to enable completions."
fi

echo ""
echo "Testing completion setup..."
# Test if complete command is available
if command -v complete >/dev/null 2>&1; then
    echo "✓ Bash completion is available"
else
    echo "⚠ Warning: 'complete' command not found. You may need to install bash-completion package."
fi

echo ""
echo "Installation finished!"
echo ""
echo "Usage:"
echo "  - Type 'dejavu2-cli <TAB>' or 'dv2 <TAB>' to see available options"
echo "  - Type 'dejavu2-cli -m <TAB>' to see available models"
echo "  - Type 'dejavu2-cli -T <TAB>' to see available templates"
echo "  - Type 'dejavu2-cli -C <TAB>' to see saved conversations"
echo ""

# Offer to test immediately if not running as root
if ! $INSTALL_SYSTEM; then
    read -p "Would you like to test the completion now? (y/N): " test_now
    if [[ "$test_now" == "y" || "$test_now" == "Y" ]]; then
        echo "Sourcing completion file..."
        source "$SOURCE_FILE"
        echo "Completion activated for this session!"
        echo "Try typing 'dejavu2-cli -' and pressing TAB"
    fi
fi