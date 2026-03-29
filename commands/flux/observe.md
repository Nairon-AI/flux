---
name: flux:observe
description: Toggle or inspect the local background bug-observer runtime state.
argument-hint: "[on|off|status]"
---

# Flux Observe

Manage the local observer sidecar runtime state for this repo.

## Usage

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"

ACTION="${ARGUMENTS:-status}"
case "$ACTION" in
  on|off|status)
    "$FLUXCTL" observe "$ACTION"
    ;;
  "")
    "$FLUXCTL" observe status
    ;;
  *)
    echo "Usage: /flux:observe [on|off|status]"
    exit 1
    ;;
esac
```

## Notes

- `on` enables the observer runtime state and sets it to `idle`
- `off` disables the observer runtime state
- `status` shows the current observer mode and state-file path
