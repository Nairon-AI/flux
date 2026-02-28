#!/bin/bash
# Inject brain index at session start so the agent knows what knowledge is available.
# Adapted from brainmaxxing (https://github.com/poteto/brainmaxxing)

# Find the brain directory - check project root first, then plugin root
if [ -f "brain/index.md" ]; then
  BRAIN_INDEX="brain/index.md"
elif [ -n "$CLAUDE_PROJECT_DIR" ] && [ -f "$CLAUDE_PROJECT_DIR/brain/index.md" ]; then
  BRAIN_INDEX="$CLAUDE_PROJECT_DIR/brain/index.md"
else
  # No brain vault found - silent exit
  exit 0
fi

echo "Brain vault index - read relevant files before acting:"
echo ""
cat "$BRAIN_INDEX"
