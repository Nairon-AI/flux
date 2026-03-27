---
name: flux:reflect
description: Capture learnings from the current session into the brain vault
argument-hint: ""
---

## Step 0: Version Check (silent, non-blocking)

Run the version check script silently. If an update is available, show a brief notice but continue:

```bash
UPDATE_INFO=$(bash "${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
```

If `update_available` is true, print once at the start:
```
Flux update available (vLOCAL -> vREMOTE). Update Flux from the same source you installed it from, then restart your agent session.
```

Then continue with the command. Do NOT block or prompt - just inform.

---

# IMPORTANT: This command MUST invoke the skill `flux-reflect`

The ONLY purpose of this command is to call the `flux-reflect` skill. You MUST use that skill now.

**User request:** $ARGUMENTS

Pass the user request to the skill. The skill handles all reflection and brain-writing logic.
