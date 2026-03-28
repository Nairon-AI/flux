#!/bin/bash
# Flux Improve - Skill Installer
# Installs skills to Codex-first paths and mirrors them to legacy Claude paths.

set -e

NAME="$1"
SOURCE="$2"  # URL or local path
SCOPE="${3:-user}"  # user or project

if [ -z "$NAME" ]; then
    echo "Usage: install-skill.sh <name> [source] [scope]"
    echo "Example: install-skill.sh stagehand-e2e https://skills.sh/stagehand user"
    exit 1
fi

BACKUP_DIR="${HOME}/.flux/snapshots/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ "$SCOPE" = "project" ]; then
    PRIMARY_SKILLS_DIR=".codex/skills"
    LEGACY_SKILLS_DIR=".claude/skills"
else
    PRIMARY_SKILLS_DIR="${CODEX_HOME:-${HOME}/.codex}/skills"
    LEGACY_SKILLS_DIR="${HOME}/.claude/skills"
fi

SKILL_PATH="$PRIMARY_SKILLS_DIR/$NAME"
LEGACY_SKILL_PATH="$LEGACY_SKILLS_DIR/$NAME"

echo "Installing skill: $NAME"
echo "Scope: $SCOPE"
echo "Location: $SKILL_PATH"
echo "Legacy mirror: $LEGACY_SKILL_PATH"
echo ""

# Create skills directories
mkdir -p "$PRIMARY_SKILLS_DIR" "$LEGACY_SKILLS_DIR"

# Backup existing skill if present
if [ -d "$SKILL_PATH" ]; then
    cp -r "$SKILL_PATH" "$BACKUP_DIR/$NAME"
    echo "Backed up existing skill to $BACKUP_DIR/$NAME"
fi

if [ -d "$LEGACY_SKILL_PATH" ]; then
    cp -r "$LEGACY_SKILL_PATH" "$BACKUP_DIR/${NAME}-legacy"
    echo "Backed up legacy mirror to $BACKUP_DIR/${NAME}-legacy"
fi

sync_legacy_mirror() {
    if [ "$LEGACY_SKILL_PATH" = "$SKILL_PATH" ] || [ ! -d "$SKILL_PATH" ]; then
        return 0
    fi

    rm -rf "$LEGACY_SKILL_PATH"
    mkdir -p "$(dirname "$LEGACY_SKILL_PATH")"
    cp -r "$SKILL_PATH" "$LEGACY_SKILL_PATH"
}

# Install based on source type
if [ -z "$SOURCE" ]; then
    # No source provided - provide instructions
    echo "To install this skill:"
    echo ""
    echo "  Option 1: From skills.sh"
    echo "    Visit https://skills.sh and search for '$NAME'"
    echo "    Follow installation instructions"
    echo ""
    echo "  Option 2: Manual"
    echo "    mkdir -p $SKILL_PATH"
    echo "    # Copy SKILL.md and any other files to $SKILL_PATH"
    echo "    # Optional legacy mirror: $LEGACY_SKILL_PATH"
    echo ""
    
    cat <<EOF
{
  "success": true,
  "name": "$NAME",
  "skill_path": "$SKILL_PATH",
  "legacy_skill_path": "$LEGACY_SKILL_PATH",
  "backup_dir": "$BACKUP_DIR",
  "manual": true,
  "instructions": "Visit skills.sh or manually copy skill files"
}
EOF

elif [[ "$SOURCE" == http* ]]; then
    # URL source - could be skills.sh or GitHub
    echo "Downloading from: $SOURCE"
    
    if [[ "$SOURCE" == *"github.com"* ]]; then
        # Clone from GitHub
        git clone --depth 1 "$SOURCE" "$SKILL_PATH" 2>/dev/null || {
            echo "✗ Failed to clone from GitHub"
            exit 1
        }
        sync_legacy_mirror
        echo "✓ Cloned skill from GitHub"
    else
        # Try to download (skills.sh or other)
        echo "Note: Automatic download not supported for this URL"
        echo "Please download manually from: $SOURCE"
    fi
    
    cat <<EOF
{
  "success": true,
  "name": "$NAME",
  "source": "$SOURCE",
  "skill_path": "$SKILL_PATH",
  "legacy_skill_path": "$LEGACY_SKILL_PATH",
  "backup_dir": "$BACKUP_DIR"
}
EOF

else
    # Local path source
    if [ -d "$SOURCE" ]; then
        cp -r "$SOURCE" "$SKILL_PATH"
        sync_legacy_mirror
        echo "✓ Copied skill from local path"
        
        cat <<EOF
{
  "success": true,
  "name": "$NAME",
  "source": "$SOURCE",
  "skill_path": "$SKILL_PATH",
  "legacy_skill_path": "$LEGACY_SKILL_PATH",
  "backup_dir": "$BACKUP_DIR"
}
EOF
    else
        echo "✗ Source path not found: $SOURCE"
        exit 1
    fi
fi
