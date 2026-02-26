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

# Check if package manager is available
case "$INSTALL_TYPE" in
    brew)
        if ! command -v brew &> /dev/null; then
            echo "Error: Homebrew not found"
            echo ""
            echo "Install Homebrew first:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo ""
            echo "Then re-run /flux:improve"
            exit 1
        fi
        ;;
    npm)
        if ! command -v npm &> /dev/null; then
            echo "Error: npm not found"
            echo ""
            echo "Install Node.js/npm:"
            case "$(uname -s)" in
                Darwin*)
                    echo "  brew install node"
                    ;;
                Linux*)
                    echo "  # Use nvm (recommended):"
                    echo "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
                    echo "  nvm install node"
                    ;;
            esac
            echo ""
            echo "Then re-run /flux:improve"
            exit 1
        fi
        ;;
    cargo)
        if ! command -v cargo &> /dev/null; then
            echo "Error: Cargo/Rust not found"
            echo ""
            echo "Install Rust:"
            echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
            echo ""
            echo "Then re-run /flux:improve"
            exit 1
        fi
        ;;
esac

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
