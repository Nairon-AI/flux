---
name: flux-contribute
description: Use when contributing fixes to Flux itself or deciding whether a reported Flux issue actually needs a PR. Reproduce first, exhaust setup/workaround causes, and only create a PR for verified product bugs.
user-invocable: false
---

# Flux Contribute

Rigorous bug analysis and PR creation for Flux. **PRs are a last resort, not a first action.**

**Role**: debugger first, PR creator second
**Goal**: solve the user's problem — only create PR if Flux itself is broken

## Session Phase Tracking

On entry, set the session phase:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL session-phase set contribute
```

On completion, reset:
```bash
$FLUXCTL session-phase set idle
```

## Input

Issue description: $ARGUMENTS

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)
- Write access to Nairon-AI/flux (or fork permission for external contributors)

## Workflow

### Phase 1: Understand the Problem (MANDATORY)

**Do NOT skip this phase. Do NOT create a PR yet.**

1. **Reproduce the issue** — Run the exact command/workflow that failed
2. **Read the error** — What specifically went wrong?
3. **Check user's setup** — Are prerequisites met? Is Flux installed correctly?

Questions to answer:
- What command was run?
- What was the expected behavior?
- What actually happened?
- What's in the user's `.flux/` directory?
- Is this a fresh install or upgrade?

### Phase 2: Attempt to Solve WITHOUT a PR

**Try these first before considering a PR:**

1. **User error?** → Guide them to correct usage
   - Wrong arguments
   - Missing prerequisites (Python, jq, git)
   - Didn't run `/flux:setup` first
   - Using incompatible command combination

2. **Configuration issue?** → Help them fix their config
   - `.flux/config.json` misconfigured
   - Environment variables missing
   - Permissions issue

3. **Known limitation?** → Explain the limitation
   - Feature not yet implemented
   - Platform-specific behavior
   - Edge case not handled

4. **Can be worked around?** → Provide workaround
   - Alternative command sequence
   - Manual steps that achieve the goal

**If any of the above solve the problem, STOP HERE. No PR needed.**

### Phase 3: Confirm It's a Genuine Flux Bug

Only proceed if ALL of these are true:

- [ ] User's setup is correct
- [ ] Command was used correctly  
- [ ] No workaround exists
- [ ] The issue is reproducible
- [ ] The fix requires changing Flux source code

**Ask the user to confirm before proceeding:**

```
mcp_question({
  questions: [{
    header: "Create PR?",
    question: "I've identified this as a genuine Flux bug that requires a code change. Should I create a PR to fix it?",
    options: [
      { label: "Yes, create PR", description: "I'll clone Flux, make the fix, and submit a PR" },
      { label: "No, let me try something else", description: "I want to investigate more first" },
      { label: "Just show me the fix", description: "Show what would need to change, I'll handle it" }
    ]
  }]
})
```

If user says no or wants to see the fix first, provide guidance without creating PR.

### Phase 4: Locate and Plan the Fix

Flux structure:
```
flux/
├── commands/flux/          # Command entry points (invoke skills)
├── skills/                 # Skill implementations (the logic)
│   └── flux-*/SKILL.md     # Main skill file
│   └── flux-*/workflow.md  # Step-by-step instructions
├── agents/                 # Scout agents for /flux:prime
├── scripts/                # Python/bash utilities
├── docs/                   # Documentation
└── README.md               # Main docs
```

**Before writing any code:**
1. Identify the exact file(s) that need changes
2. Understand WHY the current code is wrong
3. Plan the minimal fix (smallest change that solves the problem)
4. Consider edge cases the fix might affect

### Phase 5: Implement and TEST the Fix

Clone Flux repo:
```bash
FLUX_REPO="/tmp/flux-fix-$(date +%s)"
gh repo clone Nairon-AI/flux "$FLUX_REPO"
cd "$FLUX_REPO"
```

Create branch:
```bash
BRANCH="fix/$(echo "$ISSUE_SLUG" | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | head -c 40)"
git checkout -b "$BRANCH"
```

Make the fix, then **TEST IT**:
```bash
# Run the flux test suite
bun test

# Or at minimum, verify the specific fix works
# by checking the changed file makes sense
```

**Do NOT proceed if tests fail or fix doesn't work.**

### Phase 6: Create PR (Only After Verification)

Commit:
```bash
git add -A
git commit -m "fix: $ISSUE_SUMMARY

- Root cause: $ROOT_CAUSE
- Fix: $WHAT_WAS_CHANGED
- Tested: $HOW_IT_WAS_VERIFIED"
```

Push and create PR:
```bash
git push -u origin "$BRANCH"

gh pr create \
  --repo Nairon-AI/flux \
  --title "fix: $ISSUE_SUMMARY" \
  --body "## Problem
$ISSUE_DESCRIPTION

## Root Cause
$ROOT_CAUSE_ANALYSIS

## Solution
$FIX_DESCRIPTION

## Testing
- [ ] Reproduced the issue before fix
- [ ] Verified fix resolves the issue
- [ ] Checked for regressions

## How to Verify
1. Upgrade Flux from the same source you installed it from
2. Test: $VERIFICATION_STEPS

---
*Created via /flux:contribute*"
```

### Phase 7: Report to User

Show:
- PR URL
- Summary of what was fixed and why
- Next steps:
  ```
  Once merged, upgrade with:
  /flux:upgrade
  ```

## Hard Rules

### NEVER Create PRs For:
- User errors (guide them instead)
- Feature requests (open GitHub issue instead)
- Untested fixes
- Issues you can't reproduce
- Problems solved by workarounds

### ALWAYS Before Creating PR:
- Reproduce the issue
- Confirm user setup is correct
- Get explicit user confirmation
- Test the fix works
- Keep changes minimal

### PR Quality Standards:
- One issue per PR
- Clear root cause analysis
- Minimal, focused changes
- Passing tests
- Verification steps included

## Gotchas

- A user problem is not automatically a Flux bug. Misuse, missing setup, or known limitations should stop the flow before PR creation.
- Never open a speculative PR just to "see if it helps". Reproduction and verification are mandatory.
- Keep the fix minimal. If you need a redesign, file or scope follow-up work instead of smuggling it into a bugfix PR.


---

## Update Check (End of Command)

**ALWAYS run at the very end of command execution:**

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
