---
name: flux:logout
description: Disconnect Flux from Universe on this machine
argument-hint: ""
---

# Flux Logout

Remove the local Universe auth token from this machine.

## Usage

```bash
# Detect plugin root
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
if [ -z "$PLUGIN_ROOT" ]; then
  # Fallback: find latest version in plugin cache
  PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
fi

python3 "${PLUGIN_ROOT}/scripts/flux-auth.py" logout
```

This is local-only and idempotent.
