#!/bin/bash
# Flux Improve - MCP Installer
# Installs an MCP server by merging config into ~/.mcp.json

set -e

# Usage: install-mcp.sh <name> <config_json>
# Example: install-mcp.sh context7 '{"command":"npx","args":["-y","@context7/mcp"]}'

NAME="$1"
CONFIG="$2"
MCP_FILE="${HOME}/.mcp.json"
BACKUP_DIR="${HOME}/.flux/snapshots/$(date +%Y%m%d-%H%M%S)"

if [ -z "$NAME" ] || [ -z "$CONFIG" ]; then
    echo "Usage: install-mcp.sh <name> <config_json>"
    echo "Example: install-mcp.sh context7 '{\"command\":\"npx\",\"args\":[\"-y\",\"@context7/mcp\"]}'"
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "Error: jq not found"
    echo ""
    echo "jq is required to manage MCP configurations."
    echo ""
    echo "Install:"
    case "$(uname -s)" in
        Darwin*)
            echo "  brew install jq"
            ;;
        Linux*)
            if command -v apt &> /dev/null; then
                echo "  sudo apt install jq"
            elif command -v dnf &> /dev/null; then
                echo "  sudo dnf install jq"
            elif command -v pacman &> /dev/null; then
                echo "  sudo pacman -S jq"
            else
                echo "  # Use your package manager to install jq"
            fi
            ;;
        *)
            echo "  # See https://jqlang.github.io/jq/download/"
            ;;
    esac
    echo ""
    echo "Then re-run /flux:improve"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup existing config
if [ -f "$MCP_FILE" ]; then
    cp "$MCP_FILE" "$BACKUP_DIR/mcp.json"
    echo "Backed up existing config to $BACKUP_DIR/mcp.json"
fi

# Create or read existing config
if [ -f "$MCP_FILE" ]; then
    EXISTING=$(cat "$MCP_FILE")
else
    EXISTING='{"mcpServers":{}}'
fi

# Validate CONFIG is valid JSON
if ! echo "$CONFIG" | jq . > /dev/null 2>&1; then
    echo "Error: Invalid JSON config provided"
    exit 1
fi

# Check if MCP already exists
if echo "$EXISTING" | jq -e ".mcpServers.\"$NAME\"" > /dev/null 2>&1; then
    echo "Warning: MCP '$NAME' already exists in config"
    echo "Updating existing configuration..."
fi

# Merge the new MCP config
NEW_CONFIG=$(echo "$EXISTING" | jq --arg name "$NAME" --argjson config "$CONFIG" \
    '.mcpServers[$name] = $config')

# Write the new config
echo "$NEW_CONFIG" | jq . > "$MCP_FILE"

echo "✓ Installed MCP: $NAME"
echo "  Config: $MCP_FILE"
echo "  Backup: $BACKUP_DIR/mcp.json"
echo ""
echo "Note: Restart Claude Code for the MCP to take effect"

# Output JSON result for script consumption
cat <<EOF
{
  "success": true,
  "name": "$NAME",
  "config_file": "$MCP_FILE",
  "backup_dir": "$BACKUP_DIR"
}
EOF
