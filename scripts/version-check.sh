#!/usr/bin/env bash
# Flux version check - compares local vs remote version
# Returns JSON with update info

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}}"
LOCAL_VERSION=$(jq -r '.version' "$PLUGIN_ROOT/.claude-plugin/plugin.json" 2>/dev/null || echo "unknown")

# Check remote version (cache for 1 hour to avoid rate limits)
CACHE_FILE="${TMPDIR:-/tmp}/flux-version-cache"
CACHE_MAX_AGE=3600

check_remote() {
  if [[ -f "$CACHE_FILE" ]]; then
    CACHE_AGE=$(($(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0)))
    if [[ $CACHE_AGE -lt $CACHE_MAX_AGE ]]; then
      cat "$CACHE_FILE"
      return
    fi
  fi
  
  # Fetch from GitHub API
  REMOTE_VERSION=$(curl -sf "https://api.github.com/repos/Nairon-AI/n-bench/releases/latest" 2>/dev/null | jq -r '.tag_name // empty' | sed 's/^v//' || echo "")
  
  if [[ -n "$REMOTE_VERSION" ]]; then
    echo "$REMOTE_VERSION" > "$CACHE_FILE"
    echo "$REMOTE_VERSION"
  else
    echo ""
  fi
}

REMOTE_VERSION=$(check_remote)

# Compare versions
UPDATE_AVAILABLE="false"
if [[ -n "$REMOTE_VERSION" && "$REMOTE_VERSION" != "$LOCAL_VERSION" ]]; then
  # Simple semver comparison (assumes format X.Y.Z)
  if [[ "$(printf '%s\n' "$LOCAL_VERSION" "$REMOTE_VERSION" | sort -V | tail -1)" == "$REMOTE_VERSION" ]]; then
    UPDATE_AVAILABLE="true"
  fi
fi

# Output JSON
cat << EOJSON
{
  "local_version": "$LOCAL_VERSION",
  "remote_version": "${REMOTE_VERSION:-unknown}",
  "update_available": $UPDATE_AVAILABLE,
  "update_command": "/plugin marketplace update nairon-flux"
}
EOJSON
