# Update Check (Include in all skills)

At the END of every command execution, check for Flux updates:

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
```

**If update is available**, show notification at the very end of output:

```
---
Flux update available: vX.Y.Z → vA.B.C
Run: /plugin marketplace update nairon-flux
Then restart Claude Code for changes to take effect.
---
```

**If no update**, show nothing (silent).

This ensures users always know when a new version exists without manually checking changelogs.
