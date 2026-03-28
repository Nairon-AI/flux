#!/bin/bash
# Flux helper - Install PlaTo so Flux can use secure skill installs.

set -euo pipefail

TARGET="${1:-stable}"
REQUESTED_AGENT="${2:-auto}" # auto, codex, claude, skip
INSTALLER_URL="${PLATO_INSTALLER_URL:-https://raw.githubusercontent.com/Alt5r/Plato/main/scripts/install.sh}"

refresh_path() {
    local npm_prefix=""
    npm_prefix="$(npm prefix -g 2>/dev/null || true)"
    if [ -n "$npm_prefix" ] && [ -d "$npm_prefix/bin" ]; then
        export PATH="$npm_prefix/bin:$PATH"
    fi
    hash -r 2>/dev/null || true
}

resolve_agent() {
    case "$REQUESTED_AGENT" in
        codex|claude|skip)
            echo "$REQUESTED_AGENT"
            return 0
            ;;
        auto)
            if command -v codex >/dev/null 2>&1; then
                echo "codex"
            elif command -v claude >/dev/null 2>&1; then
                echo "claude"
            else
                echo "skip"
            fi
            return 0
            ;;
        *)
            echo "skip"
            return 0
            ;;
    esac
}

refresh_path

if command -v secureskills >/dev/null 2>&1; then
    cat <<EOF
{
  "success": true,
  "already_installed": true,
  "target": "$TARGET",
  "default_agent": "$(resolve_agent)",
  "command": "secureskills"
}
EOF
    exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
    echo "Error: curl is required to install PlaTo" >&2
    exit 1
fi

PLATO_DEFAULT_AGENT="$(resolve_agent)"
export PLATO_DEFAULT_AGENT

echo "Installing PlaTo for secure Flux skill installs..."
echo "Target: $TARGET"
echo "Default agent hook: $PLATO_DEFAULT_AGENT"
echo ""

if curl -fsSL "$INSTALLER_URL" | bash -s -- "$TARGET"; then
    refresh_path
    if command -v secureskills >/dev/null 2>&1; then
        cat <<EOF
{
  "success": true,
  "already_installed": false,
  "target": "$TARGET",
  "default_agent": "$PLATO_DEFAULT_AGENT",
  "command": "secureskills"
}
EOF
        exit 0
    fi
fi

echo "Error: PlaTo installation completed but 'secureskills' is still unavailable in PATH" >&2
echo "Open a new terminal or run 'exec zsh', then retry." >&2
exit 1
