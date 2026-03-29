#!/bin/bash
# Flux Improve - Installation Verification
# Verifies that installed tools are working

set -e

NAME="$1"
VERIFY_TYPE="$2"  # command_exists, config_exists, mcp_connect, skill_exists, manual
VERIFY_ARG="$3"   # command name, config path, project root, or test command
HELPER_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

ENV_JSON=$(
    python3 "$HELPER_ROOT/scripts/fluxctl.py" env --json 2>/dev/null ||
    echo '{"success":false,"primary_driver":{"name":"unknown"},"guidance":{"restart":"Restart your agent session after Flux updates or MCP/instruction-file changes.","verify":"Run `scripts/fluxctl doctor --json`."}}'
)
PRIMARY_DRIVER=$(echo "$ENV_JSON" | jq -r '.primary_driver.name // "unknown"' 2>/dev/null || echo "unknown")
RESTART_NOTE=$(echo "$ENV_JSON" | jq -r '.guidance.restart // "Restart your agent session after Flux updates or MCP/instruction-file changes."' 2>/dev/null || echo "Restart your agent session after Flux updates or MCP/instruction-file changes.")
VERIFY_HINT=$(echo "$ENV_JSON" | jq -r '.guidance.verify // "Run `scripts/fluxctl doctor --json`."' 2>/dev/null || echo 'Run `scripts/fluxctl doctor --json`.')

if [ -z "$NAME" ] || [ -z "$VERIFY_TYPE" ]; then
    echo "Usage: verify-install.sh <name> <type> [arg]"
    echo "Types: command_exists, config_exists, mcp_connect, skill_exists, manual"
    echo ""
    echo "Examples:"
    echo "  verify-install.sh jq command_exists jq"
    echo "  verify-install.sh biome config_exists biome.json"
    echo "  verify-install.sh context7 mcp_connect"
    echo "  verify-install.sh baseline-ui skill_exists /path/to/repo"
    echo "  verify-install.sh raycast manual"
    exit 1
fi

echo "Verifying: $NAME"
echo "Type: $VERIFY_TYPE"
echo ""

case "$VERIFY_TYPE" in
    command_exists)
        CMD="${VERIFY_ARG:-$NAME}"
        if command -v "$CMD" &> /dev/null; then
            VERSION=$("$CMD" --version 2>/dev/null | head -1 || echo "installed")
            echo "✓ Command '$CMD' found: $VERSION"
            cat <<EOF
{
  "success": true,
  "name": "$NAME",
  "verify_type": "command_exists",
  "command": "$CMD",
  "version": "$VERSION"
}
EOF
        else
            echo "✗ Command '$CMD' not found in PATH"
            echo ""
            echo "Possible fixes:"
            echo "  - Restart your terminal"
            echo "  - Source your shell profile: source ~/.zshrc"
            echo "  - Check if installation completed successfully"
            cat <<EOF
{
  "success": false,
  "name": "$NAME",
  "verify_type": "command_exists",
  "command": "$CMD",
  "error": "Command not found"
}
EOF
            exit 1
        fi
        ;;
        
    config_exists)
        CONFIG_PATH="${VERIFY_ARG}"
        if [ -z "$CONFIG_PATH" ]; then
            echo "✗ No config path provided"
            exit 1
        fi
        
        # Expand ~ and check both local and home
        if [ -f "$CONFIG_PATH" ] || [ -f "${HOME}/$CONFIG_PATH" ] || [ -f "./$CONFIG_PATH" ]; then
            echo "✓ Config file found"
            cat <<EOF
{
  "success": true,
  "name": "$NAME",
  "verify_type": "config_exists",
  "config_path": "$CONFIG_PATH"
}
EOF
        else
            echo "✗ Config file not found: $CONFIG_PATH"
            cat <<EOF
{
  "success": false,
  "name": "$NAME",
  "verify_type": "config_exists",
  "config_path": "$CONFIG_PATH",
  "error": "Config not found"
}
EOF
            exit 1
        fi
        ;;
        
    mcp_connect)
        # Check if MCP is in config
        MCP_FILE="${HOME}/.mcp.json"
        if [ -f "$MCP_FILE" ]; then
            if cat "$MCP_FILE" | jq -e ".mcpServers.\"$NAME\"" > /dev/null 2>&1; then
                echo "✓ MCP '$NAME' found in config"
                echo ""
                echo "Note: Full verification requires restarting the active host session"
                echo "      and testing the MCP with a sample query."
                echo "      Host: $PRIMARY_DRIVER"
                echo "      Restart: $RESTART_NOTE"
                cat <<EOF
{
  "success": true,
  "name": "$NAME",
  "verify_type": "mcp_connect",
  "config_file": "$MCP_FILE",
  "primary_driver": "$PRIMARY_DRIVER",
  "note": "$RESTART_NOTE",
  "verify_hint": "$VERIFY_HINT"
}
EOF
            else
                echo "✗ MCP '$NAME' not found in $MCP_FILE"
                cat <<EOF
{
  "success": false,
  "name": "$NAME",
  "verify_type": "mcp_connect",
  "error": "MCP not in config"
}
EOF
                exit 1
            fi
        else
            echo "✗ MCP config file not found: $MCP_FILE"
            cat <<EOF
{
  "success": false,
  "name": "$NAME",
  "verify_type": "mcp_connect",
  "error": "No MCP config file"
}
EOF
            exit 1
        fi
        ;;

    skill_exists)
        ROOT="${VERIFY_ARG:-}"
        if [ -n "$ROOT" ]; then
            PRIMARY_PATH="$ROOT/.codex/skills/$NAME"
            LEGACY_PATH="$ROOT/.claude/skills/$NAME"
        else
            PRIMARY_PATH="${CODEX_HOME:-${HOME}/.codex}/skills/$NAME"
            LEGACY_PATH="${HOME}/.claude/skills/$NAME"
        fi

        if [ -d "$PRIMARY_PATH" ] || [ -d "$LEGACY_PATH" ]; then
            FOUND_PATH="$PRIMARY_PATH"
            [ -d "$FOUND_PATH" ] || FOUND_PATH="$LEGACY_PATH"
            echo "✓ Skill found: $FOUND_PATH"
            cat <<EOF
{
  "success": true,
  "name": "$NAME",
  "verify_type": "skill_exists",
  "skill_path": "$FOUND_PATH"
}
EOF
        else
            echo "✗ Skill not found: $PRIMARY_PATH or $LEGACY_PATH"
            cat <<EOF
{
  "success": false,
  "name": "$NAME",
  "verify_type": "skill_exists",
  "skill_path": "$PRIMARY_PATH",
  "legacy_skill_path": "$LEGACY_PATH",
  "error": "Skill not found"
}
EOF
            exit 1
        fi
        ;;
        
    manual)
        echo "Manual verification required for: $NAME"
        echo ""
        if [ -n "$VERIFY_ARG" ]; then
            echo "Test: $VERIFY_ARG"
        fi
        echo ""
        echo "Please verify the installation manually and confirm."
        echo "Host: $PRIMARY_DRIVER"
        echo "Restart: $RESTART_NOTE"
        cat <<EOF
{
  "success": true,
  "name": "$NAME",
  "verify_type": "manual",
  "manual": true,
  "primary_driver": "$PRIMARY_DRIVER",
  "instructions": "${VERIFY_ARG:-Verify installation manually}",
  "restart": "$RESTART_NOTE",
  "verify_hint": "$VERIFY_HINT"
}
EOF
        ;;
        
    *)
        echo "✗ Unknown verification type: $VERIFY_TYPE"
        echo "Valid types: command_exists, config_exists, mcp_connect, skill_exists, manual"
        exit 1
        ;;
esac
