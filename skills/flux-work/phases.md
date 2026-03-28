# Flow Work Phases

**State Machine**: See [docs/state-machine.md](../../docs/state-machine.md) for the formal workflow state diagram. This skill handles the `ready_for_work` → `in_progress` → `needs_completion_review` → `done` transitions.

(Branch question already asked in SKILL.md before reading this file)

**CRITICAL**: If you are about to create:
- a markdown TODO list,
- a task list outside `.flux/`,
- or any plan files outside `.flux/`,

**STOP** and instead:
- create/update tasks in `.flux/` using `fluxctl`,
- record details in the epic/task spec markdown.

## Setup

**CRITICAL: fluxctl is BUNDLED — NOT installed globally.** `which fluxctl` will fail (expected). Always use:

```bash
FLUXCTL="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}/scripts/fluxctl"
```

## Phase 1: Resolve Input

Detect input type in this order (first match wins):

1. **Flow task ID** `fn-N-slug.M` (e.g., fn-1-add-oauth.3) or legacy `fn-N.M`/`fn-N-xxx.M` → **SINGLE_TASK_MODE**
2. **Flow epic ID** `fn-N-slug` (e.g., fn-1-add-oauth) or legacy `fn-N`/`fn-N-xxx` → **EPIC_MODE**
3. **Spec file** `.md` path that exists on disk → **EPIC_MODE**
4. **Idea text** everything else → **EPIC_MODE**

**Track the mode** — it controls looping in Phase 3.

---

**Flow task ID (fn-N-slug.M or legacy fn-N.M/fn-N-xxx.M)** → SINGLE_TASK_MODE:
- Read task: `$FLUXCTL show <id> --json`
- Read spec: `$FLUXCTL cat <id>`
- Get epic from task data for context: `$FLUXCTL show <epic-id> --json && $FLUXCTL cat <epic-id>`
- Read architecture status: `$FLUXCTL architecture status --json`
- **This is the only task to execute** — no loop to next task

**Flow epic ID (fn-N-slug or legacy fn-N/fn-N-xxx)** → EPIC_MODE:
- Read epic: `$FLUXCTL show <id> --json`
- Read spec: `$FLUXCTL cat <id>`
- Get first ready task: `$FLUXCTL ready --epic <id> --json`
- Read architecture status: `$FLUXCTL architecture status --json`

**Spec file start (.md path that exists)**:
1. Check file exists: `test -f "<path>"` — if not, treat as idea text
2. Initialize: `$FLUXCTL init --json`
3. Read file and extract title from first `# Heading` or use filename
4. Create epic: `$FLUXCTL epic create --title "<extracted-title>" --json`
5. Set spec from file: `$FLUXCTL epic set-plan <epic-id> --file <path> --json`
6. Create single task: `$FLUXCTL task create --epic <epic-id> --title "Implement <title>" --json`
7. Continue with epic-id

**Spec-less start (idea text)**:
1. Initialize: `$FLUXCTL init --json`
2. Create epic: `$FLUXCTL epic create --title "<idea>" --json`
3. Create single task: `$FLUXCTL task create --epic <epic-id> --title "Implement <idea>" --json`
4. Continue with epic-id

### Linear Status Sync

Flux syncs task status to Linear using the team's **actual workflow states** — not hardcoded values. Each Linear team has custom states (e.g., "Backlog", "Ready for Dev", "In Progress", "In Review", "QA", "Done").

**On first Linear sync for this epic**, fetch and cache the team's workflow states:

```bash
LINEAR_MAP=".flux/epics/${EPIC_ID}/linear.json"
if [ -f "$LINEAR_MAP" ]; then
  # Check if we already cached workflow states
  STATES_CACHED=$(jq -r '.workflow_states // empty' "$LINEAR_MAP")
  if [ -z "$STATES_CACHED" ]; then
    # Fetch workflow states for this team
    # Call: mcp_linear_list_workflow_states(team: LINEAR_TEAM_ID)
    # This returns states like: Backlog, Todo, In Progress, In Review, Done, Cancelled
    # Cache them in linear.json for future use
  fi
fi
```

**State mapping** — Flux maps its lifecycle events to the closest matching team state:

| Flux event | Match strategy |
|---|---|
| Task started | Find state containing "progress" or "in progress" (case-insensitive). Fallback: "started", "active" |
| Task done | Find state containing "done" or "complete" (case-insensitive). Fallback: "closed" |
| Task blocked | Find state containing "block" (case-insensitive). Fallback: skip sync |

**If no match is found** for a status, skip the sync silently — don't guess. The user can configure explicit mappings in `.flux/config.json`:

```json
{
  "linear": {
    "statusMap": {
      "in_progress": "In Development",
      "done": "Ready for QA",
      "blocked": "Blocked"
    }
  }
}
```

If `linear.statusMap` exists in config, use those exact state names instead of auto-matching.

**Epic project status** — sync the Linear project to "started" when work begins:

```bash
if [ -f "$LINEAR_MAP" ]; then
  LINEAR_PROJECT_ID=$(jq -r '.linear_project_id' "$LINEAR_MAP")
  if [ -n "$LINEAR_PROJECT_ID" ] && [ "$LINEAR_PROJECT_ID" != "null" ]; then
    # Call: mcp_linear_update_project(id: LINEAR_PROJECT_ID, state: "started")
    echo "Linear project → Started"
  fi
fi
```

## Phase 2: Apply Branch Choice

Based on user's answer from setup questions:

- **Worktree**: use `skill: flux-worktree-kit`
- **New branch**:
  ```bash
  git checkout main && git pull origin main
  git checkout -b <branch>
  ```
- **Current branch**: proceed (user already confirmed)

## Phase 3: Task Loop

**For each task**, spawn a worker subagent with fresh context.

### 3a. Find Next Task

```bash
$FLUXCTL ready --epic <epic-id> --json
```

If no ready tasks, check for completion review gate (see 3g below).

### 3b. Start Task

```bash
$FLUXCTL start <task-id> --json
```

**Sync to Linear** (if Linear integration is configured for this epic):

```bash
LINEAR_MAP=".flux/epics/${EPIC_ID}/linear.json"
if [ -f "$LINEAR_MAP" ]; then
  LINEAR_ISSUE_ID=$(jq -r ".task_mapping[\"${TASK_ID}\"]" "$LINEAR_MAP")
  if [ -n "$LINEAR_ISSUE_ID" ] && [ "$LINEAR_ISSUE_ID" != "null" ]; then
    # Get the team's "in progress" state name (from config override or auto-match)
    IN_PROGRESS_STATE=$($FLUXCTL config get linear.statusMap.in_progress --json 2>/dev/null | jq -r '.value // empty')
    # If no config override, use the cached workflow states from linear.json
    # Auto-match: find state name containing "progress" (case-insensitive)
    # Call: mcp_linear_save_issue(id: LINEAR_ISSUE_ID, state: IN_PROGRESS_STATE)
    echo "Linear: ${LINEAR_ISSUE_ID} → ${IN_PROGRESS_STATE}"
  fi
fi
```

### 3c. Spawn Worker

Use the Task tool to spawn a `worker` subagent. The worker gets fresh context and handles:
- Re-anchoring (reading spec, git status)
- Reading and, when needed, updating the canonical architecture diagram
- Implementation
- Committing
- Review cycles (if enabled)
- Completing the task (fluxctl done)

**TDD Mode Detection**: Before spawning the worker, check if TDD mode is requested:
- `--tdd` flag was passed to `/flux:work`
- Task spec mentions "TDD", "test-driven", or "red-green"
- User explicitly asked for TDD during feel-check or adapt-plan

If TDD mode: invoke `/flux:tdd <task-id>` instead of spawning the standard worker. TDD skill handles the full red-green-refactor cycle and marks the task done. After TDD completes, continue to 3d as normal.

**Prompt template for worker (standard mode):**

Pass config values only. Worker reads worker.md for phases. Do NOT paraphrase or add step-by-step instructions - worker.md has them.

```
Implement flux task.

TASK_ID: fn-X.Y
EPIC_ID: fn-X
FLUXCTL: /path/to/fluxctl
REVIEW_MODE: none|rp|codex
RALPH_MODE: true|false

Follow your phases in worker.md exactly.
```

**Worker returns**: Summary of implementation, files changed, test results, review verdict.

### 3d. Verify Completion

After worker returns, verify the task completed:

```bash
$FLUXCTL show <task-id> --json
```

If status is not `done`, the worker failed. Check output and retry or investigate.

**Sync to Linear** (if task is done and Linear mapping exists):

```bash
LINEAR_MAP=".flux/epics/${EPIC_ID}/linear.json"
if [ -f "$LINEAR_MAP" ]; then
  LINEAR_ISSUE_ID=$(jq -r ".task_mapping[\"${TASK_ID}\"]" "$LINEAR_MAP")
  if [ -n "$LINEAR_ISSUE_ID" ] && [ "$LINEAR_ISSUE_ID" != "null" ]; then
    # Get the team's "done" state name (from config override or auto-match)
    DONE_STATE=$($FLUXCTL config get linear.statusMap.done --json 2>/dev/null | jq -r '.value // empty')
    # If no config override, auto-match: find state name containing "done" or "complete"
    # Call: mcp_linear_save_issue(id: LINEAR_ISSUE_ID, state: DONE_STATE)
    echo "Linear: ${LINEAR_ISSUE_ID} → ${DONE_STATE}"
  fi
fi
```

### 3e. Feel Check (human-in-the-loop)

**Purpose**: Catch issues early. Small feedback loops beat big batch reviews.

After each task completes, prompt the user:

```
Task complete: <task-title>

**Quick feel check** (reply or skip):
1. Does it work? (quick manual test)
2. Does it feel right? (UX, behavior, output)
3. Anything feel off?

(Press Enter to continue, or tell me what needs tweaking)
```

**If user provides feedback**:
- Minor tweak → fix inline, amend commit
- Significant change → create follow-up task or update current task spec, re-implement
- Scope creep detected → note it, defer to later task

**If user skips**: Continue to next step.

**Why this matters**: "I still output 30x the code, but changes are small enough to keep the whole system in my head and adapt as things change." — @dillon_mulroy

### 3f. Adapt Plan Prompt

After feel check, ask:

```
**Adapt plan?**
Now that you've seen this working, does the plan still make sense?

a) Continue as planned
b) Update next task(s) based on what we learned
c) Add a new task
d) Remove/skip a planned task

(Reply or press Enter to continue)
```

**If user wants changes**:
- `b` → Show next task spec, ask what to change, update via `$FLUXCTL task set-spec`
- `c` → Ask for new task details, create via `$FLUXCTL task create`
- `d` → Ask which task, mark skipped via `$FLUXCTL skip <task-id>`

**If user continues**: Proceed to next task.

**Philosophy**: The plan is a living document. You learn by building. Adapt.

### 3g. Plan Sync (if enabled) — BOTH MODES

**Runs in SINGLE_TASK_MODE and EPIC_MODE.** Only the loop-back in 3h differs by mode.

Only run plan-sync if the task status is `done` (from step 3d). If not `done`, skip plan-sync and investigate/retry.

Check if plan-sync should run:

```bash
$FLUXCTL config get planSync.enabled --json
```

Skip unless planSync.enabled is explicitly `true` (null/false/missing = skip).

Get remaining tasks (todo status = not started yet):

```bash
$FLUXCTL tasks --epic <epic-id> --status todo --json
```

Skip if empty (no downstream tasks to update).

Extract downstream task IDs:

```bash
DOWNSTREAM=$($FLUXCTL tasks --epic <epic-id> --status todo --json | jq -r '[.[].id] | join(",")')
```

Note: Only sync to `todo` tasks. `in_progress` tasks are already being worked on - updating them mid-flight could cause confusion.

Use the Task tool to spawn the `plan-sync` subagent with this prompt:

```
Sync downstream tasks after implementation.

COMPLETED_TASK_ID: fn-X.Y
EPIC_ID: fn-X
FLUXCTL: /path/to/fluxctl
DOWNSTREAM_TASK_IDS: fn-X.3,fn-X.4,fn-X.5

Follow your phases in plan-sync.md exactly.
```

Plan-sync returns summary. Log it but don't block - task updates are best-effort.

### 3h. Loop or Finish

**IMPORTANT**: Steps 3d→3e→3f→3g ALWAYS run after worker returns, regardless of mode. Only the loop-back behavior differs:

**SINGLE_TASK_MODE**: After 3d→3g, go to Phase 4 (Quality). No loop.

**EPIC_MODE**: After 3d→3g, return to 3a for next task.

### 3i. Completion Review Gate (EPIC_MODE only)

When 3a finds no ready tasks, check if completion review is required.

**Check epic's completion review status directly:**

```bash
$FLUXCTL show <epic-id> --json | jq -r '.completion_review_status'
```

- If `ship` → review already passed, go to Phase 4
- If `unknown` or `needs_work` → needs review

**If review needed:**

1. Invoke `/flux:epic-review <epic-id>` skill
   - Pass `--review=<backend>` matching the work review backend
   - Skill handles rp/codex backend dispatch
   - Skill runs fix loop internally until SHIP verdict

2. After skill returns with SHIP:
   - Set status: `$FLUXCTL epic set-completion-review-status <epic-id> --status ship --json`
   - **Offer behavioral grill** (see Phase 3j below)
   - Go to Phase 4 (Quality)

**Note:** The epic-review skill gets SHIP from the reviewer but does NOT set the status itself. The caller (work skill or Ralph) sets `completion_review_status=ship` after successful review.

**Fix loop behavior**: Same as impl-review. If reviewer returns NEEDS_WORK:
1. Skill parses issues
2. Skill fixes code inline
3. Skill commits
4. Skill re-reviews (same chat for rp, same session for codex)
5. Repeat until SHIP

Only after SHIP does control return here. If skill outputs `<promise>RETRY</promise>`, there was a backend error - retry the skill invocation.

### 3j. Behavioral Grill (optional, after epic-review SHIP)

After epic-review returns SHIP, offer the user a behavioral stress test. This is different from epic-review (which checks code quality) — grill checks whether the *behavior* matches intent.

Prompt the user:

```
Epic review passed (SHIP). Before quality checks, would you like to grill the behavior?

/flux:grill walks every branch of the decision tree — verifying edge cases,
error states, and behavioral correctness against the epic spec.

[y/n] (Enter to skip)
```

- If **yes** → invoke `/flux:grill <epic-id>`. Grill may create new fix tasks — if it does, loop back to 3a to execute them, then re-run epic-review.
- If **no** or **skip** → proceed to Phase 4 (Quality).

**When to strongly recommend grill:**
- Epic has 5+ tasks (complex behavioral surface)
- Epic spec mentions user-facing workflows or state machines
- Epic touches auth, payments, or data integrity

---

**Why spawn a worker?**

Context optimization. Each task gets fresh context:
- No bleed from previous task implementations
- Re-anchor info stays with implementation (not lost to compaction)
- Review cycles stay isolated
- Main conversation stays lean (just summaries)

**Ralph mode**: Worker inherits `bypassPermissions` from parent. FLOW_RALPH=1 and REVIEW_RECEIPT_PATH are passed through.

**Interactive mode**: Permission prompts pass through to user. Worker runs in foreground (blocking).

## Phase 4: Quality

After all tasks complete (or periodically for large epics):

- Run relevant tests
- Run lint/format per repo. If the repo uses `lintcn`, include `npx lintcn lint` in this quality pass.
- If change is large/risky, run the quality auditor subagent:
  - Task flux:quality-auditor("Review recent changes")
- Fix critical issues
- **Browser verification (web-facing changes):** If the epic touches frontend/UI code, run `npx expect-cli` to auto-generate and execute browser tests from the git diff. This catches visual regressions and interaction bugs that unit tests miss. expect-cli requires no setup — it analyzes uncommitted changes and runs an AI-generated test plan in a real browser.

## Phase 5: Ship

**Verify all tasks done**:
```bash
$FLUXCTL show <epic-id> --json
$FLUXCTL validate --epic <epic-id> --json
```

**Final commit** (if any uncommitted changes):
```bash
git add -A
git status
git diff --staged
git commit -m "<final summary>"
```

**Do NOT close the epic here** unless the user explicitly asked.
Ralph closes done epics at the end of the loop.

Then push + open PR if user wants.

**After PR is opened**, check how to handle post-submit PR activity:

```bash
AUTOFIX_ENABLED=$($FLUXCTL config get autofix.enabled --json 2>/dev/null | jq -r '.value // empty')
REVIEW_BOT=$($FLUXCTL config get review.bot --json 2>/dev/null | jq -r '.value // empty')
```

**If `autofix.enabled` is `true`** → invoke `/flux:autofix {PR_URL}` automatically. This is non-blocking — auto-fix runs remotely in the cloud and handles everything: CI failures, human review comments, and bot review comments (Greptile/CodeRabbit). Reflect continues independently.

**If `autofix.enabled` is NOT `true` but `review.bot` is set** (`greptile` or `coderabbit`) → run the BYORB self-heal loop locally against the PR. The PR now exists, so the bot can review it. Follow the External Bot Self-Heal Phase from `flux-epic-review/workflow.md` (poll for bot comments, filter by severity, fix, push, re-poll — max 2 iterations). This is the fallback for users without Claude web/mobile.

**If neither is configured** → proceed directly to Reflect.

## Definition of Done

Confirm before ship:
- All tasks have status "done"
- `$FLUXCTL validate --epic <id>` passes
- Tests pass
- Lint/format pass
- Docs updated if needed
- Working tree is clean

## Example flow

```
Phase 1 (resolve) → Phase 2 (branch) → Phase 3:
  ├─ 3a-c: find task → start → spawn worker (or /flux:tdd if TDD mode)
  ├─ 3d: verify done
  ├─ 3e: FEEL CHECK (human tests, gut check)
  ├─ 3f: ADAPT PLAN (update tasks based on learnings)
  ├─ 3g: plan-sync (if enabled + downstream tasks exist)
  ├─ 3h: EPIC_MODE? → loop to 3a | SINGLE_TASK_MODE? → Phase 4
  ├─ no more tasks → 3i: check completion_review_status
  │   ├─ status != ship → invoke /flux:epic-review → fix loop until SHIP → set status=ship
  │   └─ status = ship → 3j: offer /flux:grill (behavioral stress test)
  │       ├─ yes → grill → gaps? → create fix tasks → loop to 3a
  │       └─ no → Phase 4
  └─ Phase 4 (quality) → Phase 5 (ship)
      └─ PR opened:
          ├─ autofix.enabled? → /flux:autofix (cloud, handles everything) → Reflect
          ├─ !autofix + review.bot? → BYORB local self-heal (bot comments only, max 2) → Reflect
          └─ neither → Reflect
```

## Philosophy: Tight Loops, Not Waterfall

> "Don't fall for the trap of waterfall development - our industry learned this lesson two decades ago. You can't know and plan everything upfront - neither can agents." — @dillon_mulroy

The feel-check and adapt-plan steps exist because:
1. **Small changes** keep the system in your head
2. **Frequent feedback** catches issues before they compound
3. **Living plans** adapt to reality as you learn
4. **Human judgment** on "feel" can't be automated

This is NOT about slowing down. It's about **staying fast by staying small**.
