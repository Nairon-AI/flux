#!/bin/bash
# Flux Improve - Preferences Management
# Manage dismissed recommendations and user alternatives

set -e

PREFS_FILE="$HOME/.flux/preferences.json"

# Ensure directory exists
mkdir -p "$(dirname "$PREFS_FILE")"

# Initialize preferences if not exists
init_prefs() {
    if [ ! -f "$PREFS_FILE" ]; then
        echo '{"dismissed":[],"alternatives":{},"always_allow_sessions":false,"last_updated":""}' > "$PREFS_FILE"
    fi
}

# Enable/disable always allow sessions
set_sessions() {
    local value="$1"
    init_prefs
    
    local updated=$(jq --argjson val "$value" '
        .always_allow_sessions = $val |
        .last_updated = (now | strftime("%Y-%m-%dT%H:%M:%SZ"))
    ' "$PREFS_FILE")
    
    echo "$updated" > "$PREFS_FILE"
    if [ "$value" = "true" ]; then
        echo "Session analysis: always allowed"
    else
        echo "Session analysis: will ask each time"
    fi
}

# Dismiss a recommendation (don't show again)
dismiss() {
    local name="$1"
    init_prefs
    
    local updated=$(jq --arg name "$name" '
        .dismissed = (.dismissed + [$name] | unique) |
        .last_updated = (now | strftime("%Y-%m-%dT%H:%M:%SZ"))
    ' "$PREFS_FILE")
    
    echo "$updated" > "$PREFS_FILE"
    echo "Dismissed: $name"
}

# Add alternative (user has equivalent tool)
add_alternative() {
    local recommendation="$1"
    local alternative="$2"
    init_prefs
    
    local updated=$(jq --arg rec "$recommendation" --arg alt "$alternative" '
        .alternatives[$rec] = $alt |
        .dismissed = (.dismissed + [$rec] | unique) |
        .last_updated = (now | strftime("%Y-%m-%dT%H:%M:%SZ"))
    ' "$PREFS_FILE")
    
    echo "$updated" > "$PREFS_FILE"
    echo "Added alternative: $recommendation -> $alternative"
}

# List all preferences
list() {
    init_prefs
    cat "$PREFS_FILE" | jq .
}

# Clear all preferences
clear() {
    echo '{"dismissed":[],"alternatives":{},"last_updated":""}' > "$PREFS_FILE"
    echo "Preferences cleared"
}

# Remove a dismissal (show recommendation again)
undismiss() {
    local name="$1"
    init_prefs
    
    local updated=$(jq --arg name "$name" '
        .dismissed = (.dismissed | map(select(. != $name))) |
        del(.alternatives[$name]) |
        .last_updated = (now | strftime("%Y-%m-%dT%H:%M:%SZ"))
    ' "$PREFS_FILE")
    
    echo "$updated" > "$PREFS_FILE"
    echo "Undismissed: $name"
}

# Usage
usage() {
    cat <<EOF
Flux Preferences Manager

Usage:
  $0 dismiss <name>              Don't recommend this again
  $0 alternative <rec> <alt>     I use <alt> instead of <rec>
  $0 undismiss <name>            Show recommendation again
  $0 list                        Show all preferences
  $0 clear                       Clear all preferences
  $0 sessions always             Always allow session analysis
  $0 sessions ask                Ask each time (default)

Examples:
  $0 dismiss granola             # Don't recommend Granola
  $0 alternative granola otter   # I use Otter instead of Granola
  $0 sessions always             # Never ask about sessions again
EOF
}

# Main
case "${1:-}" in
    dismiss)
        [ -z "${2:-}" ] && { echo "Error: name required"; exit 1; }
        dismiss "$2"
        ;;
    alternative)
        [ -z "${2:-}" ] || [ -z "${3:-}" ] && { echo "Error: recommendation and alternative required"; exit 1; }
        add_alternative "$2" "$3"
        ;;
    undismiss)
        [ -z "${2:-}" ] && { echo "Error: name required"; exit 1; }
        undismiss "$2"
        ;;
    list)
        list
        ;;
    clear)
        clear
        ;;
    sessions)
        case "${2:-}" in
            always) set_sessions true ;;
            ask)    set_sessions false ;;
            *)      echo "Usage: $0 sessions always|ask"; exit 1 ;;
        esac
        ;;
    *)
        usage
        ;;
esac
