#!/bin/bash
# Flux Improve - Plugin Installer
# Prints Claude Code slash-command install instructions

set -e

NAME="$1"
REPO="$2"  # e.g., "Nairon-AI/flux" or full GitHub URL

if [ -z "$NAME" ]; then
    echo "Usage: install-plugin.sh <name> [repo_or_url]"
    echo "Example: install-plugin.sh flux Nairon-AI/flux"
    exit 1
fi

BACKUP_DIR="${HOME}/.flux/snapshots/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup plugin list
if [ -d "${HOME}/.claude/plugins" ]; then
    ls "${HOME}/.claude/plugins/cache" 2>/dev/null > "$BACKUP_DIR/plugins.txt" || true
fi

echo "Preparing install instructions for plugin: $NAME"
echo ""

TARGET="${REPO:-$NAME}"

# Normalize install source for /plugin add
# Supported inputs:
# - owner/repo
# - owner/repo@tag
# - https://github.com/owner/repo
# - https://github.com/owner/repo@tag
if [[ "$TARGET" =~ ^https?:// ]]; then
    SOURCE="$TARGET"
elif [[ "$TARGET" =~ ^github\.com/ ]]; then
    SOURCE="https://$TARGET"
elif [[ "$TARGET" =~ ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+(@[^[:space:]]+)?$ ]]; then
    SOURCE="https://github.com/$TARGET"
else
    SOURCE="$TARGET"
fi

if [[ "$SOURCE" == https://github.com/* ]] && [[ "$SOURCE" != *@* ]]; then
    SOURCE="${SOURCE}@latest"
fi

INSTALL_CMD="/plugin add $SOURCE"

echo "Run this slash command directly in Claude Code input (NOT in bash):"
echo ""
echo "  $INSTALL_CMD"
echo ""
echo "Then fully restart Claude Code so the plugin loads at session start."

echo "Note: Slash commands must be run in Claude Code chat, not a shell."

# Output JSON result
cat <<EOF
{
  "success": true,
  "name": "$NAME",
  "repo": "${REPO:-null}",
  "install_command": "$INSTALL_CMD",
  "install_source": "$SOURCE",
  "backup_dir": "$BACKUP_DIR",
  "manual": true,
  "instructions": "Run the slash command in Claude Code chat input and restart Claude Code"
}
EOF
