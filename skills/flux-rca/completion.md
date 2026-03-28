# RCA Completion

## Step 12: Summary

```
## RCA Summary

**Bug**: [one sentence description]
**Severity**: [Quick / Standard / Critical]
**Root cause**: [one sentence — at the source, not the symptom]
**Production trigger**: [the real operating condition that made it fail]
**Fix**: [what was changed and where]
**Investigation**: [Flux RCA / RepoPrompt Investigate]
**Regression test**: [added / manual checklist (no test infra)]
**Pitfall written**: [.flux/brain/pitfalls/slug.md]
**Prevention**: [lint rule / type constraint / CI check / none needed]
**Similar patterns found**: [N other locations flagged / none]

Confidence: [High / Medium / Low]
```

After showing summary, offer to create PR:
> "Ready to create a PR for this fix? I'll include the root cause analysis in the PR description so reviewers have full context."

Create PR with:
- **Title**: `fix: [concise bug description]`
- **Body**: Full RCA summary + root cause chain + what was changed + regression test details

## Update Check (End of Command)

**ALWAYS run at the very end of `/flux:rca` execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
LOCAL_VER=$(echo "$UPDATE_JSON" | jq -r '.local_version')
REMOTE_VER=$(echo "$UPDATE_JSON" | jq -r '.remote_version')
```

**If update available**, append to output:

```
---
Flux update available: v${LOCAL_VER} → v${REMOTE_VER}
Update Flux from the same source you installed it from, then restart your agent session.
---
```

**If no update**: Show nothing.
