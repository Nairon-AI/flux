#!/bin/bash
# Flux Improve - Session Analysis Script
# Analyzes recent Claude Code sessions for pain points and patterns
# Delegates to parse-sessions.py for full analysis

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration (can be overridden via environment)
DAYS_BACK="${NBENCH_SESSION_DAYS:-7}"
MAX_SESSIONS="${NBENCH_SESSION_MAX:-50}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo '{"enabled":false,"reason":"Python3 not available"}'
    exit 0
fi

# Run the Python parser
exec python3 "${SCRIPT_DIR}/parse-sessions.py" --days "$DAYS_BACK" --max-sessions "$MAX_SESSIONS" "$@"
