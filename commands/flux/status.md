---
name: flux:status
description: Show Flux ↔ Universe connection state
argument-hint: "[--format text|json]"
---

# Flux Status

Show whether Flux is connected to Universe on this machine.

## Usage

```bash
# Detect plugin root
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
if [ -z "$PLUGIN_ROOT" ]; then
  # Fallback: find latest version in plugin cache
  PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
fi

python3 "${PLUGIN_ROOT}/scripts/flux-auth.py" status $ARGUMENTS
```

## Arguments

- `--format text|json` - Output format (default: text)
