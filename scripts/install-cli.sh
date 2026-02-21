#!/bin/bash
# Flux Improve - CLI Tool Installer
# Installs CLI tools via brew, npm, or direct commands

set -e

NAME="$1"
INSTALL_CMD="$2"
INSTALL_TYPE="${3:-manual}"  # brew, npm, or manual

if [ -z "$NAME" ] || [ -z "$INSTALL_CMD" ]; then
    echo "Usage: install-cli.sh <name> <install_command> [type]"
    echo "Example: install-cli.sh jq 'brew install jq' brew"
    exit 1
fi

BACKUP_DIR="${HOME}/.flux/snapshots/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Installing CLI tool: $NAME"
echo "Command: $INSTALL_CMD"
echo "Type: $INSTALL_TYPE"
echo ""

# Check if already installed
if command -v "$NAME" &> /dev/null; then
    EXISTING_VERSION=$("$NAME" --version 2>/dev/null | head -1 || echo "unknown")
    echo "Note: $NAME is already installed (version: $EXISTING_VERSION)"
    echo ""
fi

# Execute the install command
echo "Running installation..."
echo "$ $INSTALL_CMD"
echo ""

# Run the command
if eval "$INSTALL_CMD"; then
    echo ""
    echo "✓ Installation completed"
    
    # Verify installation
    if command -v "$NAME" &> /dev/null; then
        NEW_VERSION=$("$NAME" --version 2>/dev/null | head -1 || echo "installed")
        echo "✓ Verified: $NAME is now available ($NEW_VERSION)"
        SUCCESS=true
    else
        echo "⚠ Warning: $NAME not found in PATH after installation"
        echo "  You may need to restart your terminal or source your profile"
        SUCCESS=true  # Installation succeeded, just not in PATH yet
    fi
else
    echo ""
    echo "✗ Installation failed"
    SUCCESS=false
fi

# Output JSON result
cat <<EOF
{
  "success": $SUCCESS,
  "name": "$NAME",
  "install_type": "$INSTALL_TYPE",
  "backup_dir": "$BACKUP_DIR"
}
EOF
