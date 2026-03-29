# Update Check (Include in all skills)

At the END of every command execution, check for Flux updates:

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
UPDATE_CMD=$(echo "$UPDATE_JSON" | jq -r '.update_command // "Update Flux from the same source you installed it from, then restart your agent session."')
```

**If update is available**, show notification at the very end of output:

```
---
Flux update available: vX.Y.Z → vA.B.C
${UPDATE_CMD}
---
```

**If no update**, show nothing (silent).

This ensures users always know when a new version exists without manually checking changelogs.
