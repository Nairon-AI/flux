---
name: flux-autofix
description: Enable Claude's optional cloud auto-fix on a PR after submit. Watches for CI failures and review comments, pushes fixes remotely so you can walk away. Runs automatically after /flux:work submits a PR (when enabled via /flux:setup). Also invocable manually via /flux:autofix.
user-invocable: true
---

# Auto-Fix — Cloud PR Babysitting

Hands off a submitted PR to Claude's optional cloud auto-fix. Claude watches the PR remotely — fixing CI failures and addressing review comments — so you can walk away and come back to a green, ready-to-merge PR.

> "This happens remotely so you can fully walk away and come back to a ready-to-go PR." — @noahzweben

**Autonomous by default.** When enabled via `/flux:setup` (`autofix.enabled: true`), auto-fix activates automatically after every `/flux:work` PR submit. No question asked — it just runs. Can also be invoked manually on any PR.

## Session Phase Tracking

On entry, set the session phase:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
[ ! -d "$PLUGIN_ROOT/scripts" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
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
- Claude web or mobile access (auto-fix runs in the cloud, not locally)

## How It Works

Claude's auto-fix subscribes to GitHub activity on the PR. When a check fails or a reviewer leaves a comment, Claude investigates and pushes a fix:

- **Clear fixes** (lint errors, type errors, test assertion mismatches): Claude fixes, pushes, and re-runs CI automatically
- **Ambiguous requests** (architectural comments, multi-interpretation feedback): Claude asks you before acting
- **Duplicate/no-action events**: Claude notes them and moves on

Review comment replies are posted using **your GitHub account** but labeled as coming from Claude.

## Input

Full request: $ARGUMENTS

Accepts:
- No arguments (uses the most recently submitted PR from the current branch)
- A PR URL (e.g., `https://github.com/org/repo/pull/123`)
- A PR number (e.g., `#123` or `123`)

## Workflow

### Step 0: Check if enabled (manual invocation only)

When invoked automatically from `/flux:work` Phase 5, the config is already checked before invoking this skill — skip this step.

When invoked manually (`/flux:autofix`), always continue regardless of config — the user explicitly wants auto-fix on this PR.

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

### Step 2: Start cloud auto-fix session

Auto-fix works by spawning an independent cloud session via `claude --remote`. If `--remote` fails (Claude GitHub App not installed, auth issue, etc.), `claude` will return an error — the skill logs it and continues to Reflect without blocking. This creates a new Claude session on Anthropic's infrastructure that clones the repo, subscribes to GitHub events on the PR, and runs autonomously. The local session continues to Reflect — both run in parallel.

```bash
# Verify claude CLI supports --remote
claude --help 2>&1 | grep -q "\-\-remote" && echo "remote supported" || echo "no remote"
```

**If `--remote` is supported** (standard path):

```bash
claude --remote "Watch this PR and auto-fix any CI failures or review comments. Only address NEW activity — CI check failures and review comments posted after this point. Do not re-address bot comments (Greptile, CodeRabbit) that were already resolved in earlier commits. PR: ${PR_URL}"
```

Tell the user:
```
Auto-fix session started for: {PR_URL}

A separate Claude session is now running in the cloud. It will:
  - Fix CI failures (test errors, lint issues, type errors)
  - Address review comments from human reviewers
  - Handle bot feedback (Greptile/CodeRabbit) if configured
  - Push fixes and re-run CI

You can walk away — the session runs independently.
Monitor it: run /tasks in the CLI, or open claude.ai/code.
```

**If `--remote` is NOT supported** (older CLI version or a non-Claude agent):

Auto-fix cannot run autonomously without `--remote`. Tell the user:

```
Auto-fix requires `claude --remote` which isn't available in your CLI version.

Options:
  1. Update Claude: npm i -g @anthropic-ai/claude-code@latest
     Then auto-fix will work automatically on next PR submit.

  2. Start it manually from the web:
     - Open claude.ai/code
     - Paste: {PR_URL}
     - Say: "Watch this PR and auto-fix any CI failures or review comments"

  3. Start it from mobile:
     - Open the Claude mobile app
     - Say: "Watch {PR_URL} and auto-fix CI failures and review comments"

Proceeding to Reflect — auto-fix is not running for this PR.
```

In this case, skip auto-fix and continue to Reflect. Do NOT block the workflow.

### Step 3: Continue to Reflect

Auto-fix is non-blocking. Whether it started successfully or not, the local session continues:

- If invoked automatically from `/flux:work` → return control to the work skill, which proceeds to Reflect
- If invoked manually (`/flux:autofix`) → offer next steps:

```
Auto-fix is running independently. What's next?

a) /flux:reflect — capture learnings while context is fresh
b) /flux:scope — start new work
c) Done for now
```

## When Auto-Fix Runs Automatically

Auto-fix fires once per epic, at the end of `/flux:work` Phase 5 (Ship) — immediately after the PR is created. The PR is always created at the end of the epic (after all tasks → epic review → quality → Ship). There is no earlier PR creation point in the standard Flux flow.

The `claude --remote` call spawns an independent cloud session. The local session continues to Reflect in parallel. Both run independently — the cloud session watches the PR, the local session captures learnings.

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
- This is the fallback for users without Claude web/mobile

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
- Review comment replies appear under **your** GitHub username but are labeled as from Claude
- Auto-fix is best for mechanical fixes (CI failures, clear review feedback). For architectural discussions, Claude will ask before acting
- If you're already in a Claude web session that created the PR, just click "Auto-fix" in the CI status bar instead
- Auto-fix does NOT replace epic review or adversarial review — those catch code quality issues before submit. Auto-fix handles the post-submit lifecycle (CI, human reviews, bot comments).
- Auto-fix and BYORB self-heal are **mutually exclusive**. When auto-fix is enabled, BYORB is skipped entirely — auto-fix handles bot comments post-submit. When auto-fix is disabled, BYORB runs locally after submit as a fallback (max 2 iterations, bot comments only).
- **Ralph mode**: auto-fix still fires automatically after PR submit when `autofix.enabled: true`. Two autonomous processes run in parallel — Ralph locally, auto-fix in the cloud. This is fine; they don't interfere.

## Update Check (End of Command)

**ALWAYS run at the very end of command execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
CURRENT_VERSION=$(jq -r '.version' "${PLUGIN_ROOT}/.claude-plugin/plugin.json" 2>/dev/null)
MARKETPLACE_VERSION=$(jq -r '.plugins[0].version' "${PLUGIN_ROOT}/.claude-plugin/marketplace.json" 2>/dev/null)
if [ "$CURRENT_VERSION" != "$MARKETPLACE_VERSION" ] && [ -n "$MARKETPLACE_VERSION" ]; then
  echo "Update available: v${CURRENT_VERSION} → v${MARKETPLACE_VERSION}. Run /flux:upgrade"
fi
```
