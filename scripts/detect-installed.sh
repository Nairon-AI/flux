#!/bin/bash
# Flux Improve - Installed Tools Detection
# Detects CLI tools, MCPs, plugins, and applications across platforms

set -e

WARNINGS_FILE="${TMPDIR:-/tmp}/flux-detect-installed-warnings-$$.txt"
: > "$WARNINGS_FILE"

cleanup() {
    rm -f "$WARNINGS_FILE"
}

trap cleanup EXIT

add_warning() {
    printf '%s\n' "$1" >> "$WARNINGS_FILE"
}

warnings_json() {
    if [ ! -s "$WARNINGS_FILE" ]; then
        echo "[]"
        return
    fi
    jq -R . < "$WARNINGS_FILE" | jq -s .
}

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Darwin*) echo "macos" ;;
        Linux*)  echo "linux" ;;
        MINGW*|CYGWIN*|MSYS*) echo "windows" ;;
        *) echo "unknown" ;;
    esac
}

# Check if command exists
cmd_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect CLI tools
detect_cli_tools() {
    local tools=()
    
    # Essential tools
    cmd_exists jq && tools+=("jq")
    cmd_exists fzf && tools+=("fzf")
    cmd_exists rg && tools+=("ripgrep")
    cmd_exists fd && tools+=("fd")
    
    # Git tools
    cmd_exists gh && tools+=("gh")
    cmd_exists lefthook && tools+=("lefthook")
    cmd_exists husky && tools+=("husky")
    
    # Linters/formatters
    cmd_exists oxlint && tools+=("oxlint")
    cmd_exists biome && tools+=("biome")
    cmd_exists eslint && tools+=("eslint")
    cmd_exists prettier && tools+=("prettier")
    
    # Task tracking
    cmd_exists bd && tools+=("beads")
    
    # Package managers
    cmd_exists bun && tools+=("bun")
    cmd_exists pnpm && tools+=("pnpm")
    cmd_exists yarn && tools+=("yarn")
    
    printf '%s\n' "${tools[@]}" | jq -R . | jq -s .
}

# Detect macOS applications
detect_macos_apps() {
    local apps=()
    
    # Check /Applications
    [ -d "/Applications/Raycast.app" ] && apps+=("raycast")
    [ -d "/Applications/Granola.app" ] && apps+=("granola")
    [ -d "/Applications/Wispr Flow.app" ] && apps+=("wispr-flow")
    [ -d "/Applications/Dia.app" ] && apps+=("dia")
    [ -d "/Applications/Arc.app" ] && apps+=("arc")
    [ -d "/Applications/Figma.app" ] && apps+=("figma")
    [ -d "/Applications/Pencil.app" ] && apps+=("pencil")
    [ -d "/Applications/Excalidraw.app" ] && apps+=("excalidraw")
    [ -d "/Applications/Linear.app" ] && apps+=("linear")
    [ -d "/Applications/Notion.app" ] && apps+=("notion")
    [ -d "/Applications/Slack.app" ] && apps+=("slack")
    [ -d "/Applications/Discord.app" ] && apps+=("discord")
    [ -d "/Applications/Otter.app" ] && apps+=("otter")
    [ -d "/Applications/Fireflies.app" ] && apps+=("fireflies")
    [ -d "/Applications/RepoPrompt.app" ] && apps+=("repoprompt")
    
    # Check ~/Applications too
    [ -d "$HOME/Applications/Raycast.app" ] && apps+=("raycast")
    [ -d "$HOME/Applications/Granola.app" ] && apps+=("granola")
    
    # Deduplicate
    printf '%s\n' "${apps[@]}" | sort -u | jq -R . | jq -s .
}

# Detect Linux applications (desktop entries)
detect_linux_apps() {
    local apps=()
    local desktop_dirs=(
        "$HOME/.local/share/applications"
        "/usr/share/applications"
        "/usr/local/share/applications"
    )
    
    for dir in "${desktop_dirs[@]}"; do
        [ -d "$dir" ] || continue
        
        # Check for known apps by .desktop file
        [ -f "$dir/raycast.desktop" ] && apps+=("raycast")
        [ -f "$dir/linear.desktop" ] && apps+=("linear")
        [ -f "$dir/figma.desktop" ] && apps+=("figma")
        [ -f "$dir/slack.desktop" ] && apps+=("slack")
        [ -f "$dir/discord.desktop" ] && apps+=("discord")
    done
    
    printf '%s\n' "${apps[@]}" | sort -u | jq -R . | jq -s .
}

# Detect MCPs from ~/.mcp.json
detect_mcps() {
    local global_file="$HOME/.mcp.json"
    local local_file=".mcp.json"
    local claude_file="$HOME/.claude/settings.json"
    local global_mcps="[]"
    local local_mcps="[]"
    local claude_mcps="[]"
    local parsed_mcp_keys="[]"

    parse_mcp_keys() {
        local file="$1"
        local label="$2"
        parsed_mcp_keys="[]"
        if jq -e . "$file" >/dev/null 2>&1; then
            parsed_mcp_keys=$(jq -c '.mcpServers // {} | if type == "object" then keys else [] end' "$file" 2>/dev/null)
        else
            add_warning "Malformed MCP config: $label ($file)"
            parsed_mcp_keys="[]"
        fi
    }

    if [ -f "$global_file" ]; then
        parse_mcp_keys "$global_file" "global"
        global_mcps="$parsed_mcp_keys"
    fi

    if [ -f "$local_file" ]; then
        parse_mcp_keys "$local_file" "project"
        local_mcps="$parsed_mcp_keys"
    fi

    if [ -f "$claude_file" ]; then
        parse_mcp_keys "$claude_file" "claude-settings"
        claude_mcps="$parsed_mcp_keys"
    fi

    jq -n \
        --argjson global "$global_mcps" \
        --argjson local "$local_mcps" \
        --argjson claude "$claude_mcps" \
        '$global + $local + $claude | unique'
}

# Detect Claude Code plugins
detect_plugins() {
    local settings_file="$HOME/.claude/settings.json"
    
    if [ -f "$settings_file" ]; then
        if jq -e . "$settings_file" >/dev/null 2>&1; then
            jq -r '.plugins // [] | .[].name // empty' "$settings_file" 2>/dev/null | jq -R . | jq -s .
        else
            add_warning "Malformed Claude settings: $settings_file"
            echo "[]"
        fi
    else
        echo "[]"
    fi
}

# Load user preferences (dismissed recommendations, alternatives)
# Uses project-local .flux/preferences.json (like flow-next uses .flow/)
load_preferences() {
    local prefs_file=".flux/preferences.json"
    
    if [ -f "$prefs_file" ]; then
        if jq -e . "$prefs_file" >/dev/null 2>&1; then
            jq -c '
                if type == "object" then
                    . + {
                        dismissed: (.dismissed // [] | if type == "array" then . else [] end),
                        alternatives: (.alternatives // {} | if type == "object" then . else {} end)
                    }
                else
                    { dismissed: [], alternatives: {} }
                end
            ' "$prefs_file"
        else
            add_warning "Malformed preferences file: $prefs_file"
            echo '{"dismissed":[],"alternatives":{}}'
        fi
    else
        echo '{"dismissed":[],"alternatives":{}}'
    fi
}

# Main detection
main() {
    local os=$(detect_os)
    local cli_tools=$(detect_cli_tools)
    local mcps=$(detect_mcps)
    local plugins=$(detect_plugins)
    local preferences=$(load_preferences)
    local warnings=$(warnings_json)
    
    # OS-specific app detection
    local apps="[]"
    case "$os" in
        macos)  apps=$(detect_macos_apps) ;;
        linux)  apps=$(detect_linux_apps) ;;
        *)      apps="[]" ;;
    esac
    
    # Combine into JSON
    jq -n \
        --arg os "$os" \
        --argjson cli_tools "$cli_tools" \
        --argjson apps "$apps" \
        --argjson mcps "$mcps" \
        --argjson plugins "$plugins" \
        --argjson preferences "$preferences" \
        --argjson warnings "$warnings" \
        '{
            os: $os,
            installed: {
                cli_tools: $cli_tools,
                applications: $apps,
                mcps: $mcps,
                plugins: $plugins
            },
            preferences: $preferences,
            warnings: $warnings
        }'
}

main
