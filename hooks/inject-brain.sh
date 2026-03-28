#!/bin/bash
# Inject brain index at session start so the agent knows what knowledge is available.
# Adapted from brainmaxxing (https://github.com/poteto/brainmaxxing)

# Find the brain directory - canonical path is project-local .flux/brain/
if [ -f ".flux/brain/index.md" ]; then
  BRAIN_INDEX=".flux/brain/index.md"
elif [ -n "$CLAUDE_PROJECT_DIR" ] && [ -f "$CLAUDE_PROJECT_DIR/.flux/brain/index.md" ]; then
  BRAIN_INDEX="$CLAUDE_PROJECT_DIR/.flux/brain/index.md"
else
  # No brain vault found - silent exit
  exit 0
fi

echo "Brain vault index - read relevant files before acting:"
echo ""
cat "$BRAIN_INDEX"

# Also surface current Flux workflow state when available so new/resumed
# sessions can re-anchor on the active objective immediately.
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
if [ -z "$PLUGIN_ROOT" ]; then
  PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
fi
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"

if [ -x "$FLUXCTL" ] && [ -d ".flux" ]; then
  echo ""
  echo "Flux workflow status:"
  echo ""
  echo "Before acting on new work-like requests, realign with Flux state first."
  echo ""
  "$FLUXCTL" session-state || true
  echo ""
  "$FLUXCTL" prime-status || true
  echo ""
  "$FLUXCTL" architecture status || true
  echo ""
  "$FLUXCTL" scope-status || true
fi
