---
name: nbench-work
description: Execute a Flow epic or task systematically with git setup, task tracking, quality checks, and commit workflow. Use when implementing a plan or working through a spec. Triggers on /nbench:work with Flow IDs (fn-1-add-oauth, fn-1-add-oauth.2, or legacy fn-1, fn-1.2, fn-1-xxx, fn-1-xxx.2).
user-invocable: false
---

# Flow work

Execute a plan with tight feedback loops. Ship small, feel it, adapt.

> "I still output 30x the code, but changes are small enough to still let me keep the whole system in my head and adapt as things change." — @dillon_mulroy

**Core loop**:
1. Implement one task (small, atomic)
2. Feel check (human tests it, gut check)
3. Adapt plan (update based on learnings)
4. Repeat

Follow this skill and linked workflows exactly. Deviations cause drift, bad gates, retries, and user frustration.

**IMPORTANT**: This plugin uses `.flux/` for ALL task tracking. Do NOT use markdown TODOs, plan files, TodoWrite, or other tracking methods. All task state must be read and written via `nbenchctl`.

**CRITICAL: nbenchctl is BUNDLED — NOT installed globally.** `which nbenchctl` will fail (expected). Always use:
```bash
FLOWCTL="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/nbenchctl"
$FLOWCTL <command>
```

**Hard requirements (non-negotiable):**
- You MUST run `nbenchctl done` for each completed task and verify the task status is `done`.
- You MUST stage with `git add -A` (never list files). This ensures `.flux/` and `scripts/ralph/` (if present) are included.
- Do NOT claim completion until `nbenchctl show <task>` reports `status: done`.
- Do NOT invoke `/nbench:impl-review` until tests/Quick commands are green.

**Role**: execution lead, plan fidelity first.
**Goal**: complete every task in order with tests.

## Pre-check: Improvement nudge

Check if `/nbench:improve` was run recently (non-blocking):
```bash
LAST_IMPROVE="$HOME/.flux/last_improve"
if [[ -f "$LAST_IMPROVE" ]]; then
  LAST_DATE=$(cat "$LAST_IMPROVE")
  LAST_TS=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$LAST_DATE" +%s 2>/dev/null || date -d "$LAST_DATE" +%s 2>/dev/null || echo 0)
  NOW_TS=$(date +%s)
  DAYS_AGO=$(( (NOW_TS - LAST_TS) / 86400 ))
  if [[ $DAYS_AGO -ge 7 ]]; then
    echo "Tip: It's been ${DAYS_AGO} days since you ran /nbench:improve. New tools may help."
  fi
else
  echo "Tip: Run /nbench:improve to discover tools that match your workflow."
fi
```
Continue regardless.

## Ralph Mode Rules (always follow)

If `REVIEW_RECEIPT_PATH` is set or `FLOW_RALPH=1`:
- **Must** use `nbenchctl done` and verify task status is `done` before committing.
- **Must** stage with `git add -A` (never list files).
- **Do NOT** use TodoWrite for tracking.

## Input

Full request: $ARGUMENTS

Accepts:
- Flow epic ID `fn-N-slug` (e.g., `fn-1-add-oauth`) or legacy `fn-N`/`fn-N-xxx` to work through all tasks
- Flow task ID `fn-N-slug.M` (e.g., `fn-1-add-oauth.2`) or legacy `fn-N.M`/`fn-N-xxx.M` to work on single task
- Markdown spec file path (creates epic from file, then executes)
- Idea text (creates minimal epic + single task, then executes)
- Chained instructions like "then review with /nbench:impl-review"

Examples:
- `/nbench:work fn-1-add-oauth`
- `/nbench:work fn-1-add-oauth.3`
- `/nbench:work fn-1` (legacy formats fn-1, fn-1-xxx still supported)
- `/nbench:work docs/my-feature-spec.md`
- `/nbench:work Add rate limiting`
- `/nbench:work fn-1-add-oauth then review via /nbench:impl-review`

If no input provided, ask for it.

## FIRST: Parse Options or Ask Questions

Check configured backend:
```bash
REVIEW_BACKEND=$($FLOWCTL review-backend)
```
Returns: `ASK` (not configured), or `rp`/`codex`/`none` (configured).

### Option Parsing (skip questions if found in arguments)

Parse the arguments for these patterns. If found, use them and skip corresponding questions:

**Branch mode**:
- `--branch=current` or `--current` or "current branch" or "stay on this branch" → current branch
- `--branch=new` or `--new-branch` or "new branch" or "create branch" → new branch
- `--branch=worktree` or `--worktree` or "isolated worktree" or "worktree" → isolated worktree

**Review mode**:
- `--review=codex` or "review with codex" or "codex review" or "use codex" → Codex CLI (GPT 5.2 High)
- `--review=rp` or "review with rp" or "rp chat" or "repoprompt review" → RepoPrompt chat (via `nbenchctl rp chat-send`)
- `--review=export` or "export review" or "external llm" → export for external LLM
- `--review=none` or `--no-review` or "no review" or "skip review" → no review

### If options NOT found in arguments

**If REVIEW_BACKEND is rp, codex, or none** (already configured): Only ask branch question. Show override hint:

```
Quick setup: Where to work?
a) Current branch  b) New branch  c) Isolated worktree

(Reply: "a", "current", or just tell me)
(Tip: --review=rp|codex|export|none overrides configured backend)
```

**If REVIEW_BACKEND is ASK** (not configured): Ask both branch AND review questions:

```
Quick setup before starting:

1. **Branch** — Where to work?
   a) Current branch
   b) New branch
   c) Isolated worktree

2. **Review** — Run Carmack-level review after?
   a) Codex CLI
   b) RepoPrompt
   c) Export for external LLM
   d) None (configure later with --review flag)

(Reply: "1a 2a", "current branch, codex", or just tell me naturally)
```

Wait for response. Parse naturally — user may reply terse or ramble via voice.

**Defaults when empty/ambiguous:**
- Branch = `new`
- Review = configured backend if set, else `none` (no auto-detect fallback)

**Do NOT read files or write code until user responds.**

## Workflow

After setup questions answered, read [phases.md](phases.md) and execute each phase in order.

**Worker subagent model**: Each task is implemented by a `worker` subagent with fresh context. This prevents context bleed between tasks and keeps re-anchor info with the implementation. The main conversation handles task selection and looping; worker handles implementation, commits, and reviews.

If user chose review, pass the review mode to the worker. The worker invokes `/nbench:impl-review` after implementation and loops until SHIP.

**Completion review gate**: When all tasks in an epic are done, if `--require-completion-review` is configured (via `nbenchctl next`), the work skill invokes `/nbench:epic-review` before allowing the epic to close. This verifies the combined implementation satisfies the spec. The epic-review skill handles the fix loop internally until SHIP.

## Guardrails

- Don't start without asking branch question
- Don't start without plan/epic
- Don't skip tests
- Don't leave tasks half-done
- Never use TodoWrite for task tracking
- Never create plan files outside `.flux/`
