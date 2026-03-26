---
name: flux-autofix
description: Enable Claude Code's cloud auto-fix on a PR after submit. Watches for CI failures and review comments, pushes fixes remotely so you can walk away. Runs automatically after /flux:work submits a PR (when enabled via /flux:setup). Also invocable manually via /flux:autofix.
user-invocable: true
---

# Auto-Fix — Cloud PR Babysitting

Hands off a submitted PR to Claude Code's cloud auto-fix. Claude watches the PR remotely — fixing CI failures and addressing review comments — so you can walk away and come back to a green, ready-to-merge PR.

> "This happens remotely so you can fully walk away and come back to a ready-to-go PR." — @noahzweben

**Autonomous by default.** When enabled via `/flux:setup` (`autofix.enabled: true`), auto-fix activates automatically after every `/flux:work` PR submit. No question asked — it just runs. Can also be invoked manually on any PR.

## Session Phase Tracking

On entry, set the session phase:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
$FLUXCTL session-phase set autofix
```
On completion, reset:
```bash
$FLUXCTL session-phase set idle
```

## Prerequisites

- A PR must exist (just submitted via `/flux:work`, or user provides a PR URL)
- The [Claude GitHub App](https://github.com/apps/claude) must be installed on the repository
- Claude Code web or mobile access (auto-fix runs in the cloud, not locally)

## How It Works

Claude Code's auto-fix subscribes to GitHub activity on the PR. When a check fails or a reviewer leaves a comment, Claude investigates and pushes a fix:

- **Clear fixes** (lint errors, type errors, test assertion mismatches): Claude fixes, pushes, and re-runs CI automatically
- **Ambiguous requests** (architectural comments, multi-interpretation feedback): Claude asks you before acting
- **Duplicate/no-action events**: Claude notes them and moves on

Review comment replies are posted using **your GitHub account** but labeled as coming from Claude Code.

## Input

Full request: $ARGUMENTS

Accepts:
- No arguments (uses the most recently submitted PR from the current branch)
- A PR URL (e.g., `https://github.com/org/repo/pull/123`)
- A PR number (e.g., `#123` or `123`)

## Workflow

### Step 0: Check if enabled

When invoked automatically (from `/flux:work` Phase 5), check the config:

```bash
AUTOFIX_ENABLED=$($FLUXCTL config get autofix.enabled --json 2>/dev/null | jq -r '.value // empty')
```

- If `true` → continue
- If `false` or empty → skip silently (return without output)

When invoked manually (`/flux:autofix`), always continue regardless of config.

### Step 1: Resolve the PR

If a PR URL or number was provided, use it directly.

If no arguments, detect the current branch's PR:
```bash
PR_URL=$(gh pr view --json url -q '.url' 2>/dev/null)
```

If no PR found:
```
No PR found on the current branch. Either:
- Run /flux:work to submit a PR first
- Provide a PR URL: /flux:autofix https://github.com/org/repo/pull/123
```
Stop here.

### Step 2: Verify Claude GitHub App

Check if the Claude GitHub App is installed:
```bash
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null)
# Check for the claude app installation
gh api "repos/${REPO}/installation" 2>/dev/null && echo "installed" || echo "not found"
```

If not installed, tell the user:
```
The Claude GitHub App needs to be installed on this repository for auto-fix to work.

Install it here: https://github.com/apps/claude

After installing, re-run /flux:autofix
```
Stop here.

### Step 3: Determine auto-fix method

Check the environment to decide how to enable auto-fix:

**Option A — Claude Code CLI with `--remote`** (preferred, fully automated):

```bash
# Check if claude CLI supports --remote
claude --help 2>&1 | grep -q "\-\-remote" && echo "remote supported" || echo "no remote"
```

If `--remote` is supported:
```bash
claude --remote "Watch this PR and auto-fix any CI failures or review comments. Only address NEW activity — CI check failures and review comments posted after this point. Do not re-address bot comments (Greptile, CodeRabbit) that were already resolved in earlier commits. PR: ${PR_URL}"
```

Tell the user:
```
Auto-fix enabled remotely for: {PR_URL}

Claude is now watching this PR in the cloud. It will:
- Fix CI failures (test errors, lint issues, type errors)
- Address review comments
- Push fixes and re-run CI

You can walk away. Come back to a green PR.

To check status: open claude.ai/code and look for the active session.
```

**Option B — Manual setup** (if `--remote` not available):

Tell the user:
```
To enable auto-fix on this PR:

1. Open claude.ai/code (web) or the Claude Code mobile app
2. Paste this PR URL into a new session:

   {PR_URL}

3. Tell Claude: "Watch this PR and auto-fix any CI failures or review comments"

Claude will monitor the PR remotely — fixing CI failures and addressing
review comments — so you can walk away.

Tip: On web, you can also open the CI status bar and select "Auto-fix"
if the PR was created in a Claude Code web session.
```

### Step 4: Offer next steps

After enabling (or explaining) auto-fix:

```
What's next?

a) Continue to /flux:reflect (capture learnings while context is fresh)
b) Start new work (/flux:scope)
c) Done for now

The auto-fix session runs independently — you don't need to stay here.
```

## When Auto-Fix Is Offered Automatically

Auto-fix is offered in two places within the Flux workflow:

1. **After `/flux:work` Phase 5 (Ship)** — when a PR is pushed and opened, Flux offers to enable auto-fix before moving to Reflect
2. **After `/flux:gate`** — if staging validation finds issues that need a fix PR, auto-fix can watch that fix PR

## How Claude Responds to PR Activity

| Event | Claude's Response |
|-------|-------------------|
| CI check fails (lint, types, tests) | Investigates, pushes fix if confident, explains in session |
| Review comment (clear request) | Makes the change, pushes, replies on GitHub |
| Review comment (ambiguous/architectural) | Asks you before acting |
| Duplicate event | Notes it, moves on |
| No action needed | Notes it, moves on |

## Relationship to Other Flux Skills

| Skill | Relationship | Overlap? |
|-------|-------------|----------|
| `/flux:work` | Auto-fix activates after work submits a PR (Phase 5) | None — sequential |
| `/flux:gate` | Gate validates staging *after* merge. Auto-fix gets the PR to merge-ready state *before* merge | None — different lifecycle stages |
| `/flux:epic-review` | Epic review catches code quality issues *before* submit. Auto-fix catches CI/review issues *after* submit | **See deconfliction below** |
| `/flux:impl-review` | Impl review is per-task, local. Auto-fix is per-PR, remote | None — different scope |
| `/flux:reflect` | Reflect runs after auto-fix is enabled (they're independent) | None — independent |

### Deconfliction with Epic Review (BYORB Self-Heal) and Review Bots

Auto-fix and BYORB self-heal are **mutually exclusive** — they never both run. The routing is config-driven:

**If `autofix.enabled: true`:**
- Epic-review **skips BYORB entirely** (even if a draft PR exists)
- After submit, auto-fix owns the full post-submit lifecycle: CI failures, human review comments, AND bot review comments (Greptile/CodeRabbit)
- This is the better path — cloud-based, unlimited iterations, handles everything in one place

**If `autofix.enabled: false` (or unset):**
- Epic-review skips BYORB as usual (no PR exists yet in the default flow)
- After submit, Phase 5 (Ship) runs BYORB locally against the now-existing PR — polls for bot comments, self-heals (max 2 iterations)
- This is the fallback for users without Claude Code web/mobile

```
autofix.enabled: true                    autofix.enabled: false
─────────────────────                    ──────────────────────
epic-review:                             epic-review:
  adversarial review                       adversarial review
  STRIDE security scan                     STRIDE security scan
  BYORB → SKIPPED                          BYORB → SKIPPED (no PR)
  browser QA                               browser QA

quality → submit (PR created)            quality → submit (PR created)
                                           ↓
auto-fix (cloud, unlimited):             BYORB runs HERE (local, max 2 iterations):
  ✓ CI failures                            ✓ Greptile/CodeRabbit comments
  ✓ Human review comments                  ✗ CI failures (not handled)
  ✓ Greptile/CodeRabbit comments           ✗ Human reviews (not handled)

reflect → done                           reflect → done
```

**What each mechanism exclusively owns:**

| Concern | autofix.enabled: true | autofix.enabled: false |
|---------|----------------------|----------------------|
| Code quality | Adversarial review (before submit) | Adversarial review (before submit) |
| Security | STRIDE scan (before submit) | STRIDE scan (before submit) |
| Bot comments (Greptile/CodeRabbit) | Auto-fix (after submit) | BYORB (after submit, local fallback) |
| CI failures | Auto-fix (after submit) | Not handled automatically |
| Human reviewer comments | Auto-fix (after submit) | Not handled automatically |

## Gotchas

- Auto-fix requires the Claude GitHub App — it won't work without it
- Auto-fix runs remotely (cloud) — it doesn't use your local session or context window
- Review comment replies appear under **your** GitHub username but are labeled as from Claude Code
- Auto-fix is best for mechanical fixes (CI failures, clear review feedback). For architectural discussions, Claude will ask before acting
- If you're already in a Claude Code web session that created the PR, just click "Auto-fix" in the CI status bar instead
- Auto-fix does NOT replace epic review or adversarial review — those catch code quality issues before submit. Auto-fix handles the post-submit lifecycle (CI, human reviews, bot comments).
- Auto-fix and BYORB self-heal are **mutually exclusive**. When auto-fix is enabled, BYORB is skipped entirely — auto-fix handles bot comments post-submit. When auto-fix is disabled, BYORB runs locally after submit as a fallback (max 2 iterations, bot comments only).

## Update Check (End of Command)

**ALWAYS run at the very end of command execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
CURRENT_VERSION=$(jq -r '.version' "${PLUGIN_ROOT}/.claude-plugin/plugin.json" 2>/dev/null)
MARKETPLACE_VERSION=$(jq -r '.plugins[0].version' "${PLUGIN_ROOT}/.claude-plugin/marketplace.json" 2>/dev/null)
if [ "$CURRENT_VERSION" != "$MARKETPLACE_VERSION" ] && [ -n "$MARKETPLACE_VERSION" ]; then
  echo "Update available: v${CURRENT_VERSION} → v${MARKETPLACE_VERSION}. Run /flux:upgrade"
fi
```
