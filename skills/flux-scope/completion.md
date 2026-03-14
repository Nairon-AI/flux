# Completion

Post-scoping: summary, Ralph mode offer, update check, and philosophy.

---

## Summary

Show summary:

```
Epic <epic-id> created: "<title>"

Problem Statement:
"<one sentence>"

Tasks: N total | Sizes: Xs S, Ym M

Next steps:
1) Start work: /flux:work <epic-id>
2) Review the plan: /flux:plan-review <epic-id>
3) Deep dive on specific tasks: /flux:scope <task-id> --deep
```

**If Linear mode was used**, also show:
```
Linear: Synced to project "User Authentication"
Issues created: ENG-150 through ENG-154
View: https://linear.app/team/ENG/project/user-authentication
```

---

## Ralph Mode Offer

After showing the completion summary, **always** offer Ralph mode. This lets the user run the entire epic autonomously overnight.

### Step 1: Check if Ralph has been initialized

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
RALPH_EXISTS=$([[ -d "$REPO_ROOT/scripts/ralph" ]] && echo 1 || echo 0)
```

### Step 2: Present the offer

Show:
```
---
Run this epic autonomously overnight?

Ralph mode will work through all <N> tasks in <epic-id> without intervention —
plan review, implementation, code review, and completion review.

You start it from your terminal and check results in the morning.

[y/n]
---
```

Wait for user response (do NOT use AskUserQuestion tool). Only clear affirmative responses (y, yes, sure, yeah, ok, do it) count as yes. Anything else = no.

- If **no**: Continue to Update Check.
- If **yes**: Continue to Step 3.

### Step 3: Initialize or configure Ralph

**If RALPH_EXISTS=0 (first time):**

Execute the **full workflow** defined in `skills/flux-ralph-init/SKILL.md` (steps 1-7) inline. This is a Flux skill — follow its instructions directly, do NOT tell the user to run it themselves.

After ralph-init completes, continue to Step 4.

**If RALPH_EXISTS=1 (already initialized):**

Skip straight to Step 4.

### Step 4: Configure epic and show start instructions

Edit `scripts/ralph/config.env` — replace the `EPICS=` line with `EPICS=<epic-id>`.

Then show:
```
Ralph configured for epic <epic-id>.

To start (run from your terminal, NOT inside Claude Code):
  ./scripts/ralph/ralph.sh

Tip: run ./scripts/ralph/ralph_once.sh first to observe a single iteration.
Config: scripts/ralph/config.env
```

---

## Update Check (End of Command)

**ALWAYS run at the very end of /flux:scope execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
UPDATE_JSON=$("$PLUGIN_ROOT/scripts/version-check.sh" 2>/dev/null || echo '{"update_available":false}')
UPDATE_AVAILABLE=$(echo "$UPDATE_JSON" | jq -r '.update_available')
LOCAL_VER=$(echo "$UPDATE_JSON" | jq -r '.local_version')
REMOTE_VER=$(echo "$UPDATE_JSON" | jq -r '.remote_version')
```

**If update available**, append to output:

```
---
Flux update available: v${LOCAL_VER} → v${REMOTE_VER}
Run: /plugin uninstall flux@nairon-flux && /plugin install flux@nairon-flux
Then restart Claude Code for changes to take effect.
---
```

**If no update**: Show nothing (silent).

---

## Philosophy

> "The constraint used to be 'can we build it.' Now it's 'do we know what we're building.'"

**The bottleneck has flipped.** Agents can prototype faster than any team ever could. Execution is cheap. Clarity is the constraint.

**Specs are hypotheses, not canonical truths.** They're testable, run in parallel, and thrown away. This is the first time software engineers have been able to work this way at scale.

**Teams used to skip the first diamond.** Writing one implementation takes weeks, so you can't afford to build three approaches and compare them. You pick something plausible and commit before you can evaluate alternatives. This is why so many architecture decisions feel arbitrary in retrospect.

**Agents change the cost structure.** Working code in hours rather than weeks, against your actual codebase. When exploration is cheap, you stop guessing and start testing.

The Double Diamond forces you to:
1. **Diverge** on the problem — explore broadly (what teams couldn't afford before)
2. **Converge** on the problem — commit to one clear statement
3. **Diverge** on solutions — research options, consider alternatives
4. **Converge** on solution — create actionable tasks

**The skill that matters now:** Knowing what to build, defining boundaries, making implicit knowledge explicit, recognizing failure modes before they become production incidents.
