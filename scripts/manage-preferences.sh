#!/bin/bash
# Flux Improve - Preferences Management
# Manage dismissed recommendations and user alternatives

set -e

# Use project-local .flux/ directory (like flux uses .flow/)
PREFS_FILE=".flux/preferences.json"

# Ensure directory exists
mkdir -p "$(dirname "$PREFS_FILE")"

# Initialize preferences if not exists
init_prefs() {
    if [ ! -f "$PREFS_FILE" ]; then
        echo '{"dismissed":[],"dismissed_signals":{},"alternatives":{},"always_allow_sessions":false,"last_updated":""}' > "$PREFS_FILE"
    fi
    # Migrate: dismissed_signals from array to object (with timestamps)
    local sig_type
    sig_type=$(jq -r '.dismissed_signals | type' "$PREFS_FILE" 2>/dev/null)
    if [ "$sig_type" = "array" ]; then
        local migrated=$(jq '
            .dismissed_signals = (.dismissed_signals // [] | map({key: ., value: (now | strftime("%Y-%m-%dT%H:%M:%SZ"))}) | from_entries)
        ' "$PREFS_FILE")
        echo "$migrated" > "$PREFS_FILE"
    elif [ "$sig_type" = "null" ] || [ -z "$sig_type" ]; then
        local migrated=$(jq '. + {dismissed_signals: {}}' "$PREFS_FILE")
        echo "$migrated" > "$PREFS_FILE"
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

# Dismiss a friction signal with 7-day cooldown
# After 7 days, the signal resurfaces to check for new tooling
dismiss_signal() {
    local signal="$1"
    init_prefs

    local updated=$(jq --arg signal "$signal" '
        .dismissed_signals[$signal] = (now | strftime("%Y-%m-%dT%H:%M:%SZ")) |
        .last_updated = (now | strftime("%Y-%m-%dT%H:%M:%SZ"))
    ' "$PREFS_FILE")

    echo "$updated" > "$PREFS_FILE"
    echo "Dismissed signal: $signal (will resurface in 7 days)"
}

# Remove a signal dismissal (immediately re-enable)
undismiss_signal() {
    local signal="$1"
    init_prefs

    local updated=$(jq --arg signal "$signal" '
        del(.dismissed_signals[$signal]) |
        .last_updated = (now | strftime("%Y-%m-%dT%H:%M:%SZ"))
    ' "$PREFS_FILE")

    echo "$updated" > "$PREFS_FILE"
    echo "Undismissed signal: $signal"
}

# Check if a signal is currently in cooldown (dismissed < 7 days ago)
# Returns exit code 0 if signal is active (in cooldown, should be suppressed)
# Returns exit code 1 if signal has expired or was never dismissed (should trigger)
is_signal_dismissed() {
    local signal="$1"
    local cooldown_days="${2:-7}"
    init_prefs

    jq -e --arg signal "$signal" --argjson days "$cooldown_days" '
        .dismissed_signals[$signal] as $ts |
        if $ts == null then false
        else
            (now - ($ts | strptime("%Y-%m-%dT%H:%M:%SZ") | mktime)) < ($days * 86400)
        end
    ' "$PREFS_FILE" >/dev/null 2>&1
}

# List all preferences
list() {
    init_prefs
    cat "$PREFS_FILE" | jq .
}

# Clear all preferences
clear() {
    echo '{"dismissed":[],"dismissed_signals":{},"alternatives":{},"always_allow_sessions":false,"last_updated":""}' > "$PREFS_FILE"
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
  $0 dismiss <name>              Don't recommend this tool again
  $0 dismiss-signal <signal>     Snooze this friction signal for 7 days
  $0 is-signal-dismissed <signal>  Check if signal is in cooldown (exit 0 = yes, 1 = no)
  $0 alternative <rec> <alt>     I use <alt> instead of <rec>
  $0 undismiss <name>            Show tool recommendation again
  $0 undismiss-signal <signal>   Immediately re-enable this friction signal
  $0 list                        Show all preferences
  $0 clear                       Clear all preferences
  $0 sessions always             Always allow session analysis
  $0 sessions ask                Ask each time (default)

Friction signals:
  api_hallucination, lint_errors, css_issues, regressions,
  ci_failures, search_needed, context_forgotten, slow_builds,
  shallow_answers, edge_case_misses, outdated_docs, ui_issues

Signal cooldown:
  Dismissed signals automatically resurface after 7 days. This gives
  the ecosystem time to develop new tooling for that friction area.
  When a signal resurfaces, the user is asked if they want to search
  for new optimizations.

Examples:
  $0 dismiss granola             # Don't recommend Granola
  $0 dismiss-signal css_issues   # Snooze CSS friction for 7 days
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
    dismiss-signal)
        [ -z "${2:-}" ] && { echo "Error: signal name required"; exit 1; }
        dismiss_signal "$2"
        ;;
    is-signal-dismissed)
        [ -z "${2:-}" ] && { echo "Error: signal name required"; exit 1; }
        if is_signal_dismissed "$2"; then
            echo "Signal '$2' is in cooldown"
            exit 0
        else
            echo "Signal '$2' has expired or was never dismissed"
            exit 1
        fi
        ;;
    undismiss)
        [ -z "${2:-}" ] && { echo "Error: name required"; exit 1; }
        undismiss "$2"
        ;;
    undismiss-signal)
        [ -z "${2:-}" ] && { echo "Error: signal name required"; exit 1; }
        undismiss_signal "$2"
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
