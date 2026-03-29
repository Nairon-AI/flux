#!/bin/bash
# Flux Improve - Skill Installer
# Uses PlaTo for secure project-local installs and falls back to legacy mirrors
# for user-scoped installs.

set -euo pipefail

NAME="${1:-}"
SOURCE="${2:-}"  # URL or local path
SCOPE="${3:-user}"  # user or project
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATO_INSTALLER="$SCRIPT_DIR/install-plato.sh"
# shellcheck source=./secureskills-root.sh
source "$SCRIPT_DIR/secureskills-root.sh"

if [ -n "$SOURCE" ] && [ -z "${3:-}" ] && { [ "$SOURCE" = "project" ] || [ "$SOURCE" = "user" ]; }; then
    SCOPE="$SOURCE"
    SOURCE=""
fi

if [ -z "$NAME" ]; then
    echo "Usage: install-skill.sh <name> [source] [scope]"
    echo "Example: install-skill.sh baseline-ui https://github.com/ibelick/ui-skills project"
    exit 1
fi

BACKUP_DIR="${HOME}/.flux/snapshots/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

ensure_plato() {
    local default_agent="auto"
    if command -v codex >/dev/null 2>&1; then
        default_agent="codex"
    elif command -v claude >/dev/null 2>&1; then
        default_agent="claude"
    fi

    "$PLATO_INSTALLER" stable "$default_agent" >/dev/null
}

project_root() {
    secureskills_project_root "${1:-.}"
}

if [ "$SCOPE" = "project" ]; then
    PRIMARY_SKILLS_DIR=".codex/skills"
    LEGACY_SKILLS_DIR=".claude/skills"
else
    PRIMARY_SKILLS_DIR="${CODEX_HOME:-${HOME}/.codex}/skills"
    LEGACY_SKILLS_DIR="${HOME}/.claude/skills"
fi

PROJECT_ROOT="$(project_root)"
if [ "$SCOPE" = "project" ]; then
    ensure_secureskills_root "$PROJECT_ROOT" always
fi

SKILL_PATH="$PRIMARY_SKILLS_DIR/$NAME"
LEGACY_SKILL_PATH="$LEGACY_SKILLS_DIR/$NAME"
PLATO_STORE_PATH="$PROJECT_ROOT/.secureskills/store/$NAME"
PLATO_MANIFEST_PATH="$PLATO_STORE_PATH/manifest.json"
PLATO_STORAGE_DIR="$(secureskills_storage_dir "$PROJECT_ROOT")"

echo "Installing skill: $NAME"
echo "Scope: $SCOPE"
echo "Location: $SKILL_PATH"
echo "Legacy mirror: $LEGACY_SKILL_PATH"
if [ "$SCOPE" = "project" ]; then
    echo "Secure store: $PLATO_STORE_PATH"
    if [ "$PLATO_STORAGE_DIR" != "$PROJECT_ROOT/.secureskills" ]; then
        echo "Secure store backing dir: $PLATO_STORAGE_DIR"
    fi
fi
echo ""

# Backup existing skill if present
if [ -d "$SKILL_PATH" ]; then
    cp -r "$SKILL_PATH" "$BACKUP_DIR/$NAME"
    echo "Backed up existing skill to $BACKUP_DIR/$NAME"
fi

if [ -d "$LEGACY_SKILL_PATH" ]; then
    cp -r "$LEGACY_SKILL_PATH" "$BACKUP_DIR/${NAME}-legacy"
    echo "Backed up legacy mirror to $BACKUP_DIR/${NAME}-legacy"
fi

if [ -d "$PLATO_STORE_PATH" ]; then
    cp -r "$PLATO_STORE_PATH" "$BACKUP_DIR/${NAME}-plato"
    echo "Backed up secure store to $BACKUP_DIR/${NAME}-plato"
fi

sync_legacy_mirror() {
    if [ "$LEGACY_SKILL_PATH" = "$SKILL_PATH" ] || [ ! -d "$SKILL_PATH" ]; then
        return 0
    fi

    rm -rf "$LEGACY_SKILL_PATH"
    mkdir -p "$(dirname "$LEGACY_SKILL_PATH")"
    cp -r "$SKILL_PATH" "$LEGACY_SKILL_PATH"
}

install_with_plato() {
    if [ -z "$SOURCE" ]; then
        echo "PlaTo project installs need a concrete source repository or path."
        echo "Run manually from the project root:"
        echo "  secureskills add <source> --skill $NAME"
        echo "  secureskills enable codex"
        return 1
    fi

    ensure_plato

    echo "Installing securely with PlaTo into: $PROJECT_ROOT"
    echo "Command: secureskills add $SOURCE --skill $NAME --root $PROJECT_ROOT"
    echo ""

    secureskills add "$SOURCE" --skill "$NAME" --root "$PROJECT_ROOT"

    if command -v codex >/dev/null 2>&1; then
        secureskills enable codex --root "$PROJECT_ROOT" >/dev/null 2>&1 || true
    fi
    if command -v claude >/dev/null 2>&1; then
        secureskills enable claude --root "$PROJECT_ROOT" >/dev/null 2>&1 || true
    fi

    if [ ! -f "$PLATO_MANIFEST_PATH" ]; then
        echo "✗ PlaTo install did not produce a manifest: $PLATO_MANIFEST_PATH" >&2
        return 1
    fi

    cat <<EOF
{
  "success": true,
  "name": "$NAME",
  "source": "$SOURCE",
  "scope": "$SCOPE",
  "secure": true,
  "skill_path": "$PLATO_STORE_PATH",
  "manifest_path": "$PLATO_MANIFEST_PATH",
  "backup_dir": "$BACKUP_DIR"
}
EOF
}

# Install based on source type
if [ -z "$SOURCE" ]; then
    # No source provided - provide instructions
    echo "To install this skill:"
    echo ""
    if [ "$SCOPE" = "project" ]; then
        echo "  Preferred (secure, project-local with PlaTo)"
        echo "    secureskills add <source> --skill '$NAME'"
        echo "    secureskills enable codex"
        echo ""
    fi
    echo "  Option 1: From skills.sh or GitHub"
    echo "    Find the source repo for '$NAME'"
    echo "    Re-run install-skill.sh with that source URL"
    echo ""
    echo "  Option 2: Manual"
    mkdir -p "$PRIMARY_SKILLS_DIR" "$LEGACY_SKILLS_DIR"
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
  "instructions": "Provide a source repo/path for secure PlaTo install, or copy skill files manually"
}
EOF

elif [ "$SCOPE" = "project" ]; then
    install_with_plato

elif [[ "$SOURCE" == http* ]]; then
    # URL source - could be skills.sh or GitHub
    echo "Downloading from: $SOURCE"

    # Create legacy directories only for non-project installs.
    mkdir -p "$PRIMARY_SKILLS_DIR" "$LEGACY_SKILLS_DIR"
    
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
        mkdir -p "$PRIMARY_SKILLS_DIR" "$LEGACY_SKILLS_DIR"
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
