#!/bin/bash
# Flux Improve - Rollback Installation
# Restores from a snapshot created during installation

set -e

SNAPSHOT_ID="$1"
SNAPSHOTS_DIR="${HOME}/.flux/snapshots"

if [ -z "$SNAPSHOT_ID" ]; then
    echo "Usage: rollback.sh <snapshot_id>"
    echo ""
    echo "Available snapshots:"
    if [ -d "$SNAPSHOTS_DIR" ]; then
        ls -1t "$SNAPSHOTS_DIR" | head -10
    else
        echo "  No snapshots found"
    fi
    exit 1
fi

SNAPSHOT_DIR="$SNAPSHOTS_DIR/$SNAPSHOT_ID"

if [ ! -d "$SNAPSHOT_DIR" ]; then
    echo "✗ Snapshot not found: $SNAPSHOT_ID"
    echo ""
    echo "Available snapshots:"
    ls -1t "$SNAPSHOTS_DIR" | head -10
    exit 1
fi

echo "Rolling back from snapshot: $SNAPSHOT_ID"
echo "Snapshot contents:"
ls -la "$SNAPSHOT_DIR"
echo ""

# Track what we restored
RESTORED=()

# Restore MCP config
if [ -f "$SNAPSHOT_DIR/mcp.json" ]; then
    cp "$SNAPSHOT_DIR/mcp.json" "${HOME}/.mcp.json"
    echo "✓ Restored ~/.mcp.json"
    RESTORED+=("mcp.json")
fi

# Restore Claude settings
if [ -f "$SNAPSHOT_DIR/settings.json" ]; then
    mkdir -p "${HOME}/.claude"
    cp "$SNAPSHOT_DIR/settings.json" "${HOME}/.claude/settings.json"
    echo "✓ Restored ~/.claude/settings.json"
    RESTORED+=("settings.json")
fi

# Restore package.json
if [ -f "$SNAPSHOT_DIR/package.json" ]; then
    if [ -f "package.json" ]; then
        cp "$SNAPSHOT_DIR/package.json" "./package.json"
        echo "✓ Restored ./package.json"
        RESTORED+=("package.json")
    fi
fi

# Restore plugins list (informational)
if [ -f "$SNAPSHOT_DIR/plugins.txt" ]; then
    echo ""
    echo "Previous plugins were:"
    cat "$SNAPSHOT_DIR/plugins.txt"
    echo ""
    echo "Note: Legacy plugin rollback requires manual uninstall in the Claude plugin UI"
fi

# Restore skills
for skill_dir in "$SNAPSHOT_DIR"/*/; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        if [[ "$skill_name" != "." && "$skill_name" != ".." ]]; then
            if [[ "$skill_name" == *-plato ]]; then
                secure_skill_name="${skill_name%-plato}"
                SECURE_SKILL_DEST="./.secureskills/store/$secure_skill_name"
                mkdir -p "./.secureskills/store"
                rm -rf "$SECURE_SKILL_DEST"
                cp -r "$skill_dir" "$SECURE_SKILL_DEST"
                echo "✓ Restored secure skill: $secure_skill_name"
                RESTORED+=("secureskill:$secure_skill_name")
                continue
            fi
            CODEX_SKILL_DEST="${HOME}/.codex/skills/$skill_name"
            LEGACY_SKILL_DEST="${HOME}/.claude/skills/$skill_name"
            mkdir -p "${HOME}/.codex/skills" "${HOME}/.claude/skills"
            cp -r "$skill_dir" "$CODEX_SKILL_DEST"
            cp -r "$skill_dir" "$LEGACY_SKILL_DEST"
            echo "✓ Restored skill: $skill_name"
            RESTORED+=("skill:$skill_name")
        fi
    fi
done

echo ""
if [ ${#RESTORED[@]} -eq 0 ]; then
    echo "No files to restore from this snapshot"
else
    echo "Rollback complete. Restored ${#RESTORED[@]} item(s)."
    echo ""
    echo "Note: You may need to restart your agent session for changes to take effect."
fi

# Output JSON result
cat <<EOF
{
  "success": true,
  "snapshot_id": "$SNAPSHOT_ID",
  "restored": $(printf '%s\n' "${RESTORED[@]}" | jq -R . | jq -s .)
}
EOF
