#!/bin/bash
# N-bench Improve - Plugin Installer
# Installs Claude Code plugins via marketplace

set -e

NAME="$1"
REPO="$2"  # e.g., "Nairon-AI/n-bench" or marketplace name

if [ -z "$NAME" ]; then
    echo "Usage: install-plugin.sh <name> [repo]"
    echo "Example: install-plugin.sh nbench Nairon-AI/n-bench"
    exit 1
fi

BACKUP_DIR="${HOME}/.nbench/snapshots/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup plugin list
if [ -d "${HOME}/.claude/plugins" ]; then
    ls "${HOME}/.claude/plugins/cache" 2>/dev/null > "$BACKUP_DIR/plugins.txt" || true
fi

echo "Installing plugin: $NAME"
echo ""

# Check if this is a marketplace plugin or direct repo
if [ -n "$REPO" ]; then
    echo "To install this plugin, run in Claude Code:"
    echo ""
    echo "  /plugin marketplace add $REPO"
    echo "  /plugin install $NAME"
    echo ""
    INSTALL_CMD="/plugin marketplace add $REPO && /plugin install $NAME"
else
    echo "To install this plugin, run in Claude Code:"
    echo ""
    echo "  /plugin install $NAME"
    echo ""
    INSTALL_CMD="/plugin install $NAME"
fi

echo "Note: Plugin installation must be done within Claude Code"

# Output JSON result
cat <<EOF
{
  "success": true,
  "name": "$NAME",
  "repo": "${REPO:-null}",
  "install_command": "$INSTALL_CMD",
  "backup_dir": "$BACKUP_DIR",
  "manual": true,
  "instructions": "Run the install command in Claude Code"
}
EOF
