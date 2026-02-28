---
name: flux-sync
description: Manually trigger plan-sync to update downstream task specs after implementation drift. Use when code changes outpace specs.
user-invocable: false
---

# Manual Plan-Sync

Manually trigger plan-sync to update downstream task specs.

**CRITICAL: fluxctl is BUNDLED - NOT installed globally.** Always use:
```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
```

## Input

Arguments: $ARGUMENTS
Format: `<id> [--dry-run]`

- `<id>` - task ID `fn-N-slug.M` (or legacy `fn-N.M`, `fn-N-xxx.M`) or epic ID `fn-N-slug` (or legacy `fn-N`, `fn-N-xxx`)
- `--dry-run` - show changes without writing

## Workflow

### Step 1: Parse Arguments

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
[ -z "$PLUGIN_ROOT" ] && PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
FLUXCTL="${PLUGIN_ROOT}/scripts/fluxctl"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
```

Parse $ARGUMENTS for:
- First positional arg = `ID`
- `--dry-run` flag = `DRY_RUN` (true/false)

**Validate ID format first:**
- Must start with `fn-`
- If no ID provided: "Usage: /flux:sync <id> [--dry-run]"
- If doesn't match `fn-*` pattern: "Invalid ID format. Use fn-N-slug (epic) or fn-N-slug.M (task). Legacy fn-N, fn-N-xxx also work."

Detect ID type:
- Contains `.` (e.g., fn-1.2 or fn-1-add-oauth.2) -> task ID
- No `.` (e.g., fn-1 or fn-1-add-oauth) -> epic ID

### Step 2: Validate Environment

```bash
test -d .flow || { echo "No .flux/ found. Run fluxctl init first."; exit 1; }
```

If `.flux/` missing, output error and stop.

### Step 3: Validate ID Exists

```bash
$FLUXCTL show <ID> --json
```

If command fails:
- For task ID: "Task <id> not found. Run `fluxctl list` to see available."
- For epic ID: "Epic <id> not found. Run `fluxctl epics` to see available."

Stop on failure.

### Step 4: Find Downstream Tasks

**For task ID input:**
```bash
# Extract epic from task ID (remove .N suffix)
EPIC=$(echo "<task-id>" | sed 's/\.[0-9]*$//')

# Get all tasks in epic
$FLUXCTL tasks --epic "$EPIC" --json
```

Filter to `status: todo` or `status: blocked`. Exclude the source task itself.

**For epic ID input:**
```bash
$FLUXCTL tasks --epic "<epic-id>" --json
```

1. First, find a **source task** to anchor drift detection (agent requires `COMPLETED_TASK_ID`):
   - Prefer most recently updated task with `status: done`
   - Else: most recently updated task with `status: in_progress`
   - Else: error "No completed or in-progress tasks to sync from. Complete a task first."

2. Then filter remaining tasks to `status: todo` or `status: blocked` (these are downstream).

**If no downstream tasks:**
```
No downstream tasks to sync (all done or none exist).
```
Stop here (success, nothing to do).

### Step 5: Spawn Plan-Sync Agent

Build context and spawn via Task tool:

```
Sync task specs from <source> to downstream tasks.

COMPLETED_TASK_ID: <source task id - the input task, or selected source for epic mode>
FLUXCTL: ${PLUGIN_ROOT}/scripts/fluxctl
EPIC_ID: <epic id>
DOWNSTREAM_TASK_IDS: <comma-separated list from step 4>
DRY_RUN: <true|false>

<if DRY_RUN is true>
DRY RUN MODE: Report what would change but do NOT use Edit tool. Only analyze and report drift.
</if>
```

Use Task tool with `subagent_type: flux:plan-sync`

**Note:** `COMPLETED_TASK_ID` is always provided - for task-mode it's the input task, for epic-mode it's the source task selected in Step 4.

### Step 6: Report Results

After agent returns, format output:

**Normal mode:**
```
Plan-sync: <source> -> downstream tasks

Scanned: N tasks (<list>)
<agent summary>
```

**Dry-run mode:**
```
Plan-sync: <source> -> downstream tasks (DRY RUN)

<agent summary>

No files modified.
```

## Error Messages

| Case | Message |
|------|---------|
| No ID provided | "Usage: /flux:sync <id> [--dry-run]" |
| No `.flux/` | "No .flux/ found. Run `fluxctl init` first." |
| Invalid format | "Invalid ID format. Use fn-N-slug (epic) or fn-N-slug.M (task). Legacy fn-N, fn-N-xxx also work." |
| Task not found | "Task <id> not found. Run `fluxctl list` to see available." |
| Epic not found | "Epic <id> not found. Run `fluxctl list` to see available." |
| No source (epic mode) | "No completed or in-progress tasks to sync from. Complete a task first." |
| No downstream | "No downstream tasks to sync (all done or none exist)." |

## Rules

- **Ignores config** - `planSync.enabled` setting is for auto-trigger only; manual always runs
- **Any source status** - source task can be todo, in_progress, done, or blocked
- **Includes blocked** - downstream set includes both `todo` and `blocked` tasks
- **Reuses agent** - spawns existing plan-sync agent, no duplication


---

## Update Check (End of Command)

**ALWAYS run at the very end of command execution:**

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
Run: /plugin marketplace update nairon-flux
Then restart Claude Code for changes to take effect.
---
```
