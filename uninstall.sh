#!/bin/bash

# Uninstall script for Claude Code Voice Integration
# This script only undoes what install.sh does

echo "Claude Code Voice Integration Uninstaller"
echo "=========================================="
echo "This will only remove files installed by install.sh"
echo

# Function to ask for confirmation
confirm() {
    while true; do
        read -p "$1 (y/n): " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

# What install.sh creates
GLOBAL_EXEC="$HOME/.local/bin/claude-voice"
VOICE_DIR="$HOME/.claude/voice"

echo "Checking what install.sh installed..."
echo

if [ -f "$GLOBAL_EXEC" ]; then
    echo "✓ Global executable found: $GLOBAL_EXEC"
    HAS_GLOBAL=true
else
    echo "○ No global executable found"
    HAS_GLOBAL=false
fi

if [ -d "$VOICE_DIR" ]; then
    echo "✓ Voice module directory found: $VOICE_DIR"
    HAS_VOICE_DIR=true
else
    echo "○ No voice module directory found"
    HAS_VOICE_DIR=false
fi

echo

# If nothing is installed, exit
if [ "$HAS_GLOBAL" = false ] && [ "$HAS_VOICE_DIR" = false ]; then
    echo "No installed components found to uninstall."
    exit 0
fi

# Confirm removal of what install.sh created
if confirm "Remove installed components (executable and copied files)?"; then
    if [ "$HAS_GLOBAL" = true ]; then
        rm "$GLOBAL_EXEC"
        echo "✓ Removed global executable"
    fi
    
    if [ "$HAS_VOICE_DIR" = true ]; then
        rm -rf "$VOICE_DIR"
        echo "✓ Removed voice module directory"
    fi
    
    echo
    echo "✓ Uninstall completed!"
    echo
    echo "NOTE: This script does not remove:"
    echo "- Voice configuration file (~/.claude/voice_config.json)"
    echo "- Python packages installed separately"
    echo "- The original project directory"
    echo "- PATH modifications in your shell config"
    echo
else
    echo "Uninstall cancelled."
fi