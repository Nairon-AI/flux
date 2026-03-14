---
name: flux-recall
description: Search prior work by topic across Flux state, git history, conversation history, and project memory. Instant context recall for resuming work.
user-invocable: false
---

# Flux Recall

Find prior work on a topic and resume where you left off.

**Input:** `$ARGUMENTS` — the topic to search for (e.g. "auth", "payments", "migration")

## Rules

- Search ALL sources in parallel for speed.
- Matching is **case-insensitive** and **partial** — searching "auth" matches "authentication", "auth-middleware", etc.
- Omit sections with zero results entirely.
- Sort everything by most recent first.
- Cap each section at 10 results. If more exist, show "(N more not shown)".
- After showing results, suggest the most natural next action based on state.

---

## Step 1: Resolve context

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
FLUX_DIR="$REPO_ROOT/.flux"
FLUX_EXISTS=$([[ -d "$FLUX_DIR" ]] && echo 1 || echo 0)
TOPIC="$ARGUMENTS"
```

## Step 2: Search all sources in parallel

Execute **all available** searches simultaneously. Do NOT run them sequentially.

### Source A: Flux Epics (if FLUX_EXISTS=1)

Search `.flux/epics/*.json` for epics where `title` or `id` matches the topic.

For each match, extract: `id`, `title`, `status`, `workflow_phase`, `workflow_status`, `created_at`, `updated_at`.

### Source B: Flux Tasks (if FLUX_EXISTS=1)

Search `.flux/tasks/*.json` for tasks where `title` or `id` matches the topic.

For each match, extract: `id`, `title`, `status`, `epic` (parent epic ID), `created_at`.

### Source C: Flux Specs (if FLUX_EXISTS=1)

Search `.flux/specs/*.md` content for the topic using Grep. Return matching file names and the first matching line for context.

### Source D: Flux Memory (if FLUX_EXISTS=1)

Search `.flux/memory/*.md` content for the topic using Grep. Return matching file names and the first matching line.

### Source E: Git History

```bash
git log --oneline --all --grep="$TOPIC" -i -20
```

### Source F: Conversation History

Search `~/.claude/history.jsonl` for lines where the content matches the topic. Each line is JSON — look for the topic in the `display` field (case-insensitive). Extract the 10 most recent matches with: `display` (truncated to 80 chars), `timestamp`, `project`.

If `~/.claude/history.jsonl` does not exist, skip silently.

### Source G: Project Memory Files

Search `~/.claude/projects/*/memory/*.md` files for the topic using Grep. Return matching file paths and first matching line.

## Step 3: Present results

Format output as:

```
═══ RECALL: $TOPIC ═══════════════════════════

EPICS:
  * [epic-id] "[title]"
    Status: [status] | Phase: [workflow_phase] | Updated: [updated_at]

TASKS:
  * [task-id] "[title]"
    Status: [status] | Epic: [epic-id]

SPECS:
  * [file] — [first matching line excerpt]

FLUX MEMORY:
  * [file] — [matching context]

GIT COMMITS:
  * [hash] [message]

CONVERSATION HISTORY:
  * [timestamp] [project] — [prompt excerpt]

PROJECT MEMORY:
  * [file] — [matching context]

═══════════════════════════════════════════════
```

Omit any section that has zero results. If ALL sections are empty, show:

```
No prior work found on "$TOPIC".
Ready to start fresh — try /flux:scope to begin scoping.
```

## Step 4: Suggest next action

Based on the results, suggest the most natural next step. Pick the **first matching** rule:

1. **In-progress task matching the topic** → "Resume work: `/flux:work <task-id>`"
2. **Blocked task matching the topic** → "Blocked task found — review: `/flux:work <task-id> --force`"
3. **Open epic with todo tasks** → "Continue epic: `/flux:work <epic-id>`"
4. **Completed epic** → "This epic is done. Re-scope if needed: `/flux:scope <topic>`"
5. **Git/conversation matches only (no Flux state)** → "No active Flux work. Start scoping: `/flux:scope <topic>`"
6. **Spec matches** → "Found related specs. Review: read the matched spec files"

Show the suggestion as:

```
Next: <suggestion>
```

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
Run: /plugin uninstall flux@nairon-flux && /plugin add https://github.com/Nairon-AI/flux@latest
Then restart Claude Code for changes to take effect.
---
```
