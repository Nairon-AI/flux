---
name: nbench:improve
description: Analyze your environment and recommend workflow optimizations
argument-hint: "[--skip-sessions] [--discover] [--explain] [--category=mcp|cli|plugin|skill|pattern]"
---

## Step 0: Version Check (silent, non-blocking)

Run the version check script silently. If an update is available, show a brief notice but continue:

```bash
UPDATE_INFO=$("${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
```

If `update_available` is true, print once at the start:
```
📦 N-bench update available (vLOCAL → vREMOTE). Run: /plugin marketplace update nairon-n-bench
```

Then continue with the command. Do NOT block or prompt - just inform.

---

# IMPORTANT: This command MUST invoke the skill `nbench-improve`

The ONLY purpose of this command is to call the `nbench-improve` skill. You MUST use that skill now.

**User request:** $ARGUMENTS

Pass the user request to the skill. The skill handles all analysis and recommendation logic.
