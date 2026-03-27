---
name: flux:prime
description: Analyze codebase for agent readiness and propose improvements
argument-hint: "[--report-only] [--fix-all] [path]"
---

## Step 0: Version Check (silent, non-blocking)

Run the version check script silently. If an update is available, show a brief notice but continue:

```bash
UPDATE_INFO=$(bash "${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
```

If `update_available` is true, print once at the start:
```
📦 Flux update available (vLOCAL → vREMOTE). Update Flux from the same source you installed it from, then restart your agent session.
```

Then continue with the command. Do NOT block or prompt - just inform.

---

## Step 0.5: Mark Prime As Running

If `.flux/bin/fluxctl` exists in the current repo, run:

```bash
.flux/bin/fluxctl prime-mark --status in_progress --json >/dev/null 2>&1 || true
```

This records that prime has started, so Flux can route the session correctly while the audit is running.

---

# IMPORTANT: This command MUST invoke the skill `flux-prime`

The ONLY purpose of this command is to call the `flux-prime` skill. You MUST use that skill now.

**User request:** $ARGUMENTS

Pass the user request to the skill. The skill handles all assessment and remediation logic.

After the skill completes successfully, if `.flux/bin/fluxctl` exists, run:

```bash
.flux/bin/fluxctl prime-mark --status done --json >/dev/null 2>&1 || true
```
