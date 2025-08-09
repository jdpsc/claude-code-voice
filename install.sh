#!/bin/bash

# Install script for Claude Code Voice Integration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
VOICE_DIR="$HOME/.claude/voice"

echo "Installing Claude Code Voice Integration..."

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$VOICE_DIR"

# Copy files
cp "$SCRIPT_DIR/claude_code_voice_module.py" "$VOICE_DIR/"
cp "$SCRIPT_DIR/claude_code_voice_integration.py" "$VOICE_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$VOICE_DIR/"

# Copy and setup virtual environment
if [ -d "$SCRIPT_DIR/claude-voice-env" ]; then
    cp -r "$SCRIPT_DIR/claude-voice-env" "$VOICE_DIR/"
fi

# Create the main executable script
cat > "$INSTALL_DIR/claude-voice" << 'EOF'
#!/bin/bash

# Claude Code Voice Integration
VOICE_DIR="$HOME/.claude/voice"

# Check if virtual environment exists
if [ ! -d "$VOICE_DIR/claude-voice-env" ]; then
    echo "Error: Virtual environment not found. Please run the install script from the repository directory."
    exit 1
fi

# Run the voice-enabled Claude Code
"$VOICE_DIR/claude-voice-env/bin/python" "$VOICE_DIR/claude_code_voice_integration.py" "$@"
EOF

# Make it executable
chmod +x "$INSTALL_DIR/claude-voice"

echo "✓ Installed to $INSTALL_DIR/claude-voice"
echo ""

# Check if ~/.local/bin is already in PATH
if [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
    echo "✓ $HOME/.local/bin is already in your PATH"
    echo "You can now run: claude-voice"
else
    echo "To use claude-voice from anywhere, add this to your shell config:"
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "Then reload your shell and run: claude-voice"
fi