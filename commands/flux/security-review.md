---
name: flux:security-review
description: Comprehensive security review with STRIDE analysis and vulnerability validation
argument-hint: "[--mode pr|full|staged] [--severity high]"
---

## Step 0: Version Check (silent, non-blocking)

Run the version check script silently. If an update is available, show a brief notice but continue:

```bash
UPDATE_INFO=$("${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
```

If `update_available` is true, print once at the start:
```
Flux update available (vLOCAL -> vREMOTE). Run: /plugin marketplace update nairon-flux
```

Then continue with the command. Do NOT block or prompt - just inform.

---

# IMPORTANT: This command MUST invoke the skill `flux-security-review`

The ONLY purpose of this command is to call the `flux-security-review` skill. You MUST use that skill now.

**User request:** $ARGUMENTS

Pass the user request to the skill. The skill handles comprehensive security review with STRIDE methodology.
