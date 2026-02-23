# Flow Work Phases

(Branch question already asked in SKILL.md before reading this file)

**CRITICAL**: If you are about to create:
- a markdown TODO list,
- a task list outside `.nbench/`,
- or any plan files outside `.nbench/`,

**STOP** and instead:
- create/update tasks in `.nbench/` using `nbenchctl`,
- record details in the epic/task spec markdown.

## Setup

**CRITICAL: nbenchctl is BUNDLED — NOT installed globally.** `which nbenchctl` will fail (expected). Always use:

```bash
FLOWCTL="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}/scripts/nbenchctl"
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
- Read task: `$FLOWCTL show <id> --json`
- Read spec: `$FLOWCTL cat <id>`
- Get epic from task data for context: `$FLOWCTL show <epic-id> --json && $FLOWCTL cat <epic-id>`
- **This is the only task to execute** — no loop to next task

**Flow epic ID (fn-N-slug or legacy fn-N/fn-N-xxx)** → EPIC_MODE:
- Read epic: `$FLOWCTL show <id> --json`
- Read spec: `$FLOWCTL cat <id>`
- Get first ready task: `$FLOWCTL ready --epic <id> --json`

**Spec file start (.md path that exists)**:
1. Check file exists: `test -f "<path>"` — if not, treat as idea text
2. Initialize: `$FLOWCTL init --json`
3. Read file and extract title from first `# Heading` or use filename
4. Create epic: `$FLOWCTL epic create --title "<extracted-title>" --json`
5. Set spec from file: `$FLOWCTL epic set-plan <epic-id> --file <path> --json`
6. Create single task: `$FLOWCTL task create --epic <epic-id> --title "Implement <title>" --json`
7. Continue with epic-id

**Spec-less start (idea text)**:
1. Initialize: `$FLOWCTL init --json`
2. Create epic: `$FLOWCTL epic create --title "<idea>" --json`
3. Create single task: `$FLOWCTL task create --epic <epic-id> --title "Implement <idea>" --json`
4. Continue with epic-id

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
$FLOWCTL ready --epic <epic-id> --json
```

If no ready tasks, check for completion review gate (see 3g below).

### 3b. Start Task

```bash
$FLOWCTL start <task-id> --json
```

### 3c. Spawn Worker

Use the Task tool to spawn a `worker` subagent. The worker gets fresh context and handles:
- Re-anchoring (reading spec, git status)
- Implementation
- Committing
- Review cycles (if enabled)
- Completing the task (nbenchctl done)

**Prompt template for worker:**

Pass config values only. Worker reads worker.md for phases. Do NOT paraphrase or add step-by-step instructions - worker.md has them.

```
Implement flux task.

TASK_ID: fn-X.Y
EPIC_ID: fn-X
FLOWCTL: /path/to/nbenchctl
REVIEW_MODE: none|rp|codex
RALPH_MODE: true|false

Follow your phases in worker.md exactly.
```

**Worker returns**: Summary of implementation, files changed, test results, review verdict.

### 3d. Verify Completion

After worker returns, verify the task completed:

```bash
$FLOWCTL show <task-id> --json
```

If status is not `done`, the worker failed. Check output and retry or investigate.

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
- `b` → Show next task spec, ask what to change, update via `$FLOWCTL task set-spec`
- `c` → Ask for new task details, create via `$FLOWCTL task create`
- `d` → Ask which task, mark skipped via `$FLOWCTL skip <task-id>`

**If user continues**: Proceed to next task.

**Philosophy**: The plan is a living document. You learn by building. Adapt.

### 3g. Plan Sync (if enabled) — BOTH MODES

**Runs in SINGLE_TASK_MODE and EPIC_MODE.** Only the loop-back in 3h differs by mode.

Only run plan-sync if the task status is `done` (from step 3d). If not `done`, skip plan-sync and investigate/retry.

Check if plan-sync should run:

```bash
$FLOWCTL config get planSync.enabled --json
```

Skip unless planSync.enabled is explicitly `true` (null/false/missing = skip).

Get remaining tasks (todo status = not started yet):

```bash
$FLOWCTL tasks --epic <epic-id> --status todo --json
```

Skip if empty (no downstream tasks to update).

Extract downstream task IDs:

```bash
DOWNSTREAM=$($FLOWCTL tasks --epic <epic-id> --status todo --json | jq -r '[.[].id] | join(",")')
```

Note: Only sync to `todo` tasks. `in_progress` tasks are already being worked on - updating them mid-flight could cause confusion.

Use the Task tool to spawn the `plan-sync` subagent with this prompt:

```
Sync downstream tasks after implementation.

COMPLETED_TASK_ID: fn-X.Y
EPIC_ID: fn-X
FLOWCTL: /path/to/nbenchctl
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
$FLOWCTL show <epic-id> --json | jq -r '.completion_review_status'
```

- If `ship` → review already passed, go to Phase 4
- If `unknown` or `needs_work` → needs review

**If review needed:**

1. Invoke `/nbench:epic-review <epic-id>` skill
   - Pass `--review=<backend>` matching the work review backend
   - Skill handles rp/codex backend dispatch
   - Skill runs fix loop internally until SHIP verdict

2. After skill returns with SHIP:
   - Set status: `$FLOWCTL epic set-completion-review-status <epic-id> --status ship --json`
   - Go to Phase 4 (Quality)

**Note:** The epic-review skill gets SHIP from the reviewer but does NOT set the status itself. The caller (work skill or Ralph) sets `completion_review_status=ship` after successful review.

**Fix loop behavior**: Same as impl-review. If reviewer returns NEEDS_WORK:
1. Skill parses issues
2. Skill fixes code inline
3. Skill commits
4. Skill re-reviews (same chat for rp, same session for codex)
5. Repeat until SHIP

Only after SHIP does control return here. If skill outputs `<promise>RETRY</promise>`, there was a backend error - retry the skill invocation.

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
- Run lint/format per repo
- If change is large/risky, run the quality auditor subagent:
  - Task flux:quality-auditor("Review recent changes")
- Fix critical issues

## Phase 5: Ship

**Verify all tasks done**:
```bash
$FLOWCTL show <epic-id> --json
$FLOWCTL validate --epic <epic-id> --json
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

## Definition of Done

Confirm before ship:
- All tasks have status "done"
- `$FLOWCTL validate --epic <id>` passes
- Tests pass
- Lint/format pass
- Docs updated if needed
- Working tree is clean

## Example flow

```
Phase 1 (resolve) → Phase 2 (branch) → Phase 3:
  ├─ 3a-c: find task → start → spawn worker
  ├─ 3d: verify done
  ├─ 3e: FEEL CHECK (human tests, gut check)
  ├─ 3f: ADAPT PLAN (update tasks based on learnings)
  ├─ 3g: plan-sync (if enabled + downstream tasks exist)
  ├─ 3h: EPIC_MODE? → loop to 3a | SINGLE_TASK_MODE? → Phase 4
  ├─ no more tasks → 3i: check completion_review_status
  │   ├─ status != ship → invoke /nbench:epic-review → fix loop until SHIP → set status=ship
  │   └─ status = ship → Phase 4
  └─ Phase 4 (quality) → Phase 5 (ship)
```

## Philosophy: Tight Loops, Not Waterfall

> "Don't fall for the trap of waterfall development - our industry learned this lesson two decades ago. You can't know and plan everything upfront - neither can agents." — @dillon_mulroy

The feel-check and adapt-plan steps exist because:
1. **Small changes** keep the system in your head
2. **Frequent feedback** catches issues before they compound
3. **Living plans** adapt to reality as you learn
4. **Human judgment** on "feel" can't be automated

This is NOT about slowing down. It's about **staying fast by staying small**.
