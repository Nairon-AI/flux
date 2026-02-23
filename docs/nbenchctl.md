# nbenchctl CLI Reference

CLI for `.nbench/` task tracking. Agents must use nbenchctl for all writes.

> **Note:** This is the full human reference. Agents should read `.nbench/usage.md` (created by `/nbench:setup`).

## Available Commands

```
init, detect, epic, task, dep, show, epics, tasks, list, cat, ready, next, start, done, block, validate, config, memory, prep-chat, rp, codex, checkpoint, status, state-path, migrate-state
```

## Multi-User Safety

Works out of the box for parallel branches. No setup required.

- **ID allocation**: Scans existing files to determine next ID (merge-safe)
- **Soft claims**: Tasks have `assignee` field to prevent duplicate work
- **Actor resolution**: `FLOW_ACTOR` env → git email → git name → `$USER` → "unknown"
- **Local validation**: `nbenchctl validate --all` catches issues before commit

**Optional**: Add CI gate with `docs/ci-workflow-example.yml` to block bad PRs.

## File Structure

```
.nbench/
├── meta.json               # {schema_version, next_epic}
├── epics/fn-N-slug.json    # Epic state (e.g., fn-1-add-oauth.json)
├── specs/fn-N-slug.md      # Epic spec (markdown)
├── tasks/fn-N-slug.M.json  # Task state (e.g., fn-1-add-oauth.1.json)
├── tasks/fn-N-slug.M.md    # Task spec (markdown)
├── memory/                 # Agent memory (reserved)
├── bin/                    # (optional) Local nbenchctl install via /nbench:setup
│   ├── nbenchctl
│   └── nbenchctl.py
└── usage.md                # (optional) CLI reference via /nbench:setup
```

Flowctl accepts schema v1 and v2; new fields are optional and defaulted.

New fields:
- Epic JSON: `plan_review_status`, `plan_reviewed_at`, `completion_review_status`, `completion_reviewed_at`, `depends_on_epics`, `branch_name`, `default_impl`, `default_review`, `default_sync`
- Task JSON: `priority`, `impl`, `review`, `sync`

## ID Format

- **Epic**: `fn-N-slug` where `slug` is derived from the title (e.g., `fn-1-add-oauth`, `fn-2-fix-login-bug`)
- **Task**: `fn-N-slug.M` (e.g., `fn-1-add-oauth.1`, `fn-2-fix-login-bug.2`)

**Backwards compatibility**: Legacy formats `fn-N` (no suffix) and `fn-N-xxx` (random 3-char suffix) are still supported.

## Commands

### init

Initialize `.nbench/` directory.

```bash
nbenchctl init [--json]
```

### detect

Check if `.nbench/` exists and is valid.

```bash
nbenchctl detect [--json]
```

Output:
```json
{"success": true, "exists": true, "valid": true, "path": "/repo/.nbench"}
```

### epic create

Create new epic.

```bash
nbenchctl epic create --title "Epic title" [--branch "fn-1-epic-title"] [--json]
```

Output:
```json
{"success": true, "id": "fn-1-epic-title", "title": "Epic title", "spec_path": ".nbench/specs/fn-1-epic-title.md"}
```

### epic set-plan

Overwrite epic spec from file.

```bash
nbenchctl epic set-plan fn-1 --file plan.md [--json]
```

### epic set-plan-review-status

Set plan review status and timestamp.

```bash
nbenchctl epic set-plan-review-status fn-1 --status ship|needs_work|unknown [--json]
```

### epic set-completion-review-status

Set completion review status and timestamp.

```bash
nbenchctl epic set-completion-review-status fn-1 --status ship|needs_work|unknown [--json]
```

### epic set-branch

Set epic branch_name.

```bash
nbenchctl epic set-branch fn-1 --branch "fn-1-epic" [--json]
```

### epic close

Close epic (requires all tasks done).

```bash
nbenchctl epic close fn-1 [--json]
```

### epic set-backend

Set default backend specs for impl/review/sync workers. Used by orchestration products (e.g., flow-swarm).

```bash
nbenchctl epic set-backend fn-1 --impl codex:gpt-5.2-codex [--json]
nbenchctl epic set-backend fn-1 --impl codex:gpt-5.2-high --review claude:opus [--json]
nbenchctl epic set-backend fn-1 --impl "" [--json]  # Clear impl (inherit from config)
```

Options:
- `--impl SPEC`: Default impl backend (e.g., `codex:gpt-5.2-high`, `claude:opus`)
- `--review SPEC`: Default review backend (e.g., `claude:opus`, `agent:opus-4.5-thinking`)
- `--sync SPEC`: Default sync backend (e.g., `claude:haiku`, `gemini:gemini-2.5-flash`)

Format: `backend:model` where backend is a CLI name and model is backend-specific.

### task create

Create task under epic.

```bash
nbenchctl task create --epic fn-1 --title "Task title" [--deps fn-1.2,fn-1.3] [--acceptance-file accept.md] [--priority 10] [--json]
```

Output:
```json
{"success": true, "id": "fn-1.4", "epic": "fn-1", "title": "Task title", "depends_on": ["fn-1.2", "fn-1.3"]}
```

### task set-description

Set task description section.

```bash
nbenchctl task set-description fn-1.2 --file desc.md [--json]
```

### task set-acceptance

Set task acceptance section.

```bash
nbenchctl task set-acceptance fn-1.2 --file accept.md [--json]
```

### task set-spec

Set description and acceptance in one call (fewer writes).

```bash
nbenchctl task set-spec fn-1.2 --description desc.md --acceptance accept.md [--json]
```

Both `--description` and `--acceptance` are optional; supply one or both.

### task reset

Reset task to `todo` status, clearing assignee and completion data.

```bash
nbenchctl task reset fn-1.2 [--cascade] [--json]
```

Use `--cascade` to also reset dependent tasks within the same epic.

### task set-backend

Set backend specs for impl/review/sync workers. Used by orchestration products (e.g., flow-swarm).

```bash
nbenchctl task set-backend fn-1.1 --impl codex:gpt-5.2-high [--json]
nbenchctl task set-backend fn-1.1 --impl codex:gpt-5.2-high --review claude:opus [--json]
nbenchctl task set-backend fn-1.1 --impl "" [--json]  # Clear impl (inherit from epic/config)
```

Options:
- `--impl SPEC`: Impl backend (e.g., `codex:gpt-5.2-high`, `claude:opus`)
- `--review SPEC`: Review backend (e.g., `claude:opus`, `agent:opus-4.5-thinking`)
- `--sync SPEC`: Sync backend (e.g., `claude:haiku`, `gemini:gemini-2.5-flash`)

Format: `backend:model` where backend is a CLI name and model is backend-specific.

### task show-backend

Show effective backend specs for a task. Reports task-level and epic-level specs only (config-level resolution happens in flow-swarm).

```bash
nbenchctl task show-backend fn-1.1 [--json]
```

Output (text):
```
impl: codex:gpt-5.2-high (task)
review: claude:opus (epic)
sync: null
```

Output (json):
```json
{
  "success": true,
  "id": "fn-1.1",
  "epic": "fn-1",
  "impl": {"spec": "codex:gpt-5.2-high", "source": "task"},
  "review": {"spec": "claude:opus", "source": "epic"},
  "sync": {"spec": null, "source": null}
}
```

### dep add

Add single dependency to task.

```bash
nbenchctl dep add fn-1.3 fn-1.2 [--json]
```

Dependencies must be within same epic.

### task set-deps

Set multiple dependencies for a task (convenience command).

```bash
nbenchctl task set-deps fn-1.3 --deps fn-1.1,fn-1.2 [--json]
```

Equivalent to multiple `dep add` calls. Dependencies must be within same epic.

### show

Show epic or task details.

```bash
nbenchctl show fn-1 [--json]     # Epic with tasks
nbenchctl show fn-1.2 [--json]   # Task only
```

Epic output includes `tasks` array with id/title/status/priority/depends_on.

### epics

List all epics.

```bash
nbenchctl epics [--json]
```

Output:
```json
{"success": true, "epics": [{"id": "fn-1", "title": "...", "status": "open", "tasks": 5, "done": 2}], "count": 1}
```

Human-readable output shows progress: `[open] fn-1: Title (2/5 tasks done)`

### tasks

List tasks, optionally filtered.

```bash
nbenchctl tasks [--json]                    # All tasks
nbenchctl tasks --epic fn-1 [--json]        # Tasks for specific epic
nbenchctl tasks --status todo [--json]      # Filter by status
nbenchctl tasks --epic fn-1 --status done   # Combine filters
```

Status options: `todo`, `in_progress`, `blocked`, `done`

Output:
```json
{"success": true, "tasks": [{"id": "fn-1.1", "epic": "fn-1", "title": "...", "status": "todo", "priority": null, "depends_on": []}], "count": 1}
```

### list

List all epics with their tasks grouped together.

```bash
nbenchctl list [--json]
```

Human-readable output:
```
Flow Status: 2 epics, 5 tasks (2 done)

[open] fn-1: Add auth system (1/3 done)
    [done] fn-1.1: Create user model
    [in_progress] fn-1.2: Add login endpoint
    [todo] fn-1.3: Add logout endpoint

[open] fn-2: Add caching (1/2 done)
    [done] fn-2.1: Setup Redis
    [todo] fn-2.2: Cache API responses
```

JSON output:
```json
{"success": true, "epics": [...], "tasks": [...], "epic_count": 2, "task_count": 5}
```

### cat

Print spec markdown (no JSON mode).

```bash
nbenchctl cat fn-1      # Epic spec
nbenchctl cat fn-1.2    # Task spec
```

### ready

List tasks ready to start, in progress, and blocked.

```bash
nbenchctl ready --epic fn-1 [--json]
```

Output:
```json
{
  "success": true,
  "epic": "fn-1",
  "actor": "user@example.com",
  "ready": [{"id": "fn-1.3", "title": "...", "depends_on": []}],
  "in_progress": [{"id": "fn-1.1", "title": "...", "assignee": "user@example.com"}],
  "blocked": [{"id": "fn-1.4", "title": "...", "blocked_by": ["fn-1.2"]}]
}
```

### next

Select next plan/work unit.

```bash
nbenchctl next [--epics-file epics.json] [--require-plan-review] [--require-completion-review] [--json]
```

Output:
```json
{"status":"plan|work|completion_review|none","epic":"fn-12","task":"fn-12.3","reason":"needs_plan_review|needs_completion_review|resume_in_progress|ready_task|none|blocked_by_epic_deps","blocked_epics":{"fn-12":["fn-3"]}}
```

The `--require-completion-review` flag gates epic closure on completion review. When all tasks are done but `completion_review_status != ship`, returns `status: completion_review`.

### start

Start task (set status=in_progress). Sets assignee to current actor.

```bash
nbenchctl start fn-1.2 [--force] [--note "..."] [--json]
```

Validates:
- Status is `todo` (or `in_progress` if resuming own task)
- Status is not `blocked` unless `--force`
- All dependencies are `done`
- Not claimed by another actor

Use `--force` to skip checks and take over from another actor.
Use `--note` to add a claim note (auto-set on takeover).

### done

Complete task with summary and evidence. Requires `in_progress` status.

```bash
nbenchctl done fn-1.2 --summary-file summary.md --evidence-json evidence.json [--force] [--json]
```

Use `--force` to skip status check.

Evidence JSON format:
```json
{"commits": [], "tests": ["test_foo"], "prs": ["#42"]}
```

### block

Block a task and record a reason in the task spec.

```bash
nbenchctl block fn-1.2 --reason-file reason.md [--json]
```

### validate

Validate epic structure (specs, deps, cycles).

```bash
nbenchctl validate --epic fn-1 [--json]
nbenchctl validate --all [--json]
```

Single epic output:
```json
{"success": false, "epic": "fn-1", "valid": false, "errors": ["..."], "warnings": [], "task_count": 5}
```

All epics output:
```json
{
  "success": false,
  "valid": false,
  "epics": [{"epic": "fn-1", "valid": true, ...}],
  "total_epics": 2,
  "total_tasks": 10,
  "total_errors": 1
}
```

Checks:
- Epic/task specs exist
- Task specs have required headings
- Task statuses are valid (`todo`, `in_progress`, `blocked`, `done`)
- Dependencies exist and are within epic
- No dependency cycles
- Done status consistency

Exits with code 1 if validation fails (for CI use).

### config

Manage project configuration stored in `.nbench/config.json`.

```bash
# Get a config value
nbenchctl config get memory.enabled [--json]
nbenchctl config get review.backend [--json]

# Set a config value
nbenchctl config set memory.enabled true [--json]
nbenchctl config set review.backend codex [--json]  # rp, codex, or none

# Toggle boolean config
nbenchctl config toggle memory.enabled [--json]
```

**Available settings:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `memory.enabled` | bool | `false` | Enable memory system |
| `planSync.enabled` | bool | `false` | Enable plan-sync after task completion |
| `scouts.github` | bool | `false` | Enable github-scout during planning (requires gh CLI) |
| `review.backend` | string | `null` | Default review backend (`rp`, `codex`, `none`). If unset, review commands require `--review` or `FLOW_REVIEW_BACKEND`. |

Priority: `--review=...` argument > `FLOW_REVIEW_BACKEND` env > `.nbench/config.json` > error.

No auto-detect. Run `/nbench:setup` (or `nbenchctl config set review.backend ...`) to configure.

### memory

Manage persistent learnings in `.nbench/memory/`.

```bash
# Initialize memory directory
nbenchctl memory init [--json]

# Add entries
nbenchctl memory add --type pitfall "Always use nbenchctl rp wrappers" [--json]
nbenchctl memory add --type convention "Tests in __tests__ dirs" [--json]
nbenchctl memory add --type decision "SQLite for simplicity" [--json]

# Query
nbenchctl memory list [--json]
nbenchctl memory search "pattern" [--json]
nbenchctl memory read --type pitfalls [--json]
```

Types: `pitfall`, `convention`, `decision`

### prep-chat

Generate properly escaped JSON for RepoPrompt chat. Avoids shell escaping issues with complex prompts.
Optional legacy positional arg is ignored; do not pass epic/task IDs.

```bash
# Write message to file (avoids escaping issues)
cat > /tmp/prompt.md << 'EOF'
Your multi-line prompt with "quotes", $variables, and `backticks`.
EOF

# Generate JSON
nbenchctl prep-chat \
  --message-file /tmp/prompt.md \
  --mode chat \
  [--new-chat] \
  [--chat-name "Review Name"] \
  [--selected-paths file1.ts file2.ts] \
  [-o /tmp/payload.json]

# Prefer nbenchctl rp chat-send (uses this internally)
nbenchctl rp chat-send --window W --tab T --message-file /tmp/prompt.md
```

Options:
- `--message-file FILE` (required): File containing the message text
- `--mode {chat,ask}`: Chat mode (default: chat)
- `--new-chat`: Start a new chat session
- `--chat-name NAME`: Name for the new chat
- `--selected-paths FILE...`: Files to include in context (for follow-ups)
- `-o, --output FILE`: Write JSON to file (default: stdout)

Output (stdout or file):
```json
{"message": "...", "mode": "chat", "new_chat": true, "chat_name": "...", "selected_paths": ["..."]}
```

### rp

RepoPrompt wrappers (preferred for reviews). Requires RepoPrompt 1.5.68+.

**Primary entry point** (handles window selection + builder atomically):

```bash
# Atomic setup - picks window by repo root and creates builder tab
eval "$(nbenchctl rp setup-review --repo-root "$REPO_ROOT" --summary "Review a plan to ...")"
# Returns: W=<window> T=<tab>

# With --create: auto-creates RP window if none matches (RP 1.5.68+)
eval "$(nbenchctl rp setup-review --repo-root "$REPO_ROOT" --summary "..." --create)"
```

**Post-setup commands** (use $W and $T from setup-review):

```bash
nbenchctl rp prompt-get --window "$W" --tab "$T"
nbenchctl rp prompt-set --window "$W" --tab "$T" --message-file /tmp/review-prompt.md
nbenchctl rp select-add --window "$W" --tab "$T" path/to/file
nbenchctl rp chat-send --window "$W" --tab "$T" --message-file /tmp/review-prompt.md
nbenchctl rp prompt-export --window "$W" --tab "$T" --out /tmp/export.md
```

**Low-level commands** (prefer setup-review instead):

```bash
nbenchctl rp windows [--json]
nbenchctl rp pick-window --repo-root "$REPO_ROOT"
nbenchctl rp ensure-workspace --window "$W" --repo-root "$REPO_ROOT"
nbenchctl rp builder --window "$W" --summary "Review a plan to ..."
```

### codex

OpenAI Codex CLI wrappers — cross-platform alternative to RepoPrompt.

**Requirements:**
```bash
npm install -g @openai/codex
codex auth
```

**Model:** Uses GPT 5.2 High by default (no user config needed). Override with `FLOW_CODEX_MODEL` env var.

**Commands:**

```bash
# Verify codex is available
nbenchctl codex check [--json]

# Implementation review (reviews code changes for a task)
nbenchctl codex impl-review <task-id> --base <branch> [--sandbox <mode>] [--receipt <path>] [--json]
# Example: nbenchctl codex impl-review fn-1.3 --base main --sandbox auto --receipt /tmp/impl-fn-1.3.json

# Plan review (reviews epic spec before implementation)
nbenchctl codex plan-review <epic-id> --files <file1,file2,...> [--sandbox <mode>] [--receipt <path>] [--json]
# Example: nbenchctl codex plan-review fn-1 --files "src/auth.ts,src/config.ts" --sandbox auto --receipt /tmp/plan-fn-1.json
# Note: Epic/task specs are included automatically; --files should be CODE files for repository context.

# Completion review (reviews epic implementation against spec)
nbenchctl codex completion-review <epic-id> [--sandbox <mode>] [--receipt <path>] [--json]
# Example: nbenchctl codex completion-review fn-1 --sandbox auto --receipt /tmp/completion-fn-1.json
# Runs after all tasks done; verifies implementation matches spec requirements
```

**How it works:**

1. **Gather context hints** — Analyzes changed files, extracts symbols (functions, classes), finds references in unchanged files
2. **Build review prompt** — Uses same Carmack-level criteria as RepoPrompt (7 criteria each for plan/impl)
3. **Run codex** — Executes `codex exec` with the prompt (or `codex exec resume` for session continuity)
4. **Parse verdict** — Extracts `<verdict>SHIP|NEEDS_WORK|MAJOR_RETHINK</verdict>` from output
5. **Write receipt** — If `--receipt` provided, writes JSON for Ralph gating

**Context hints example:**
```
Changed files: src/auth.py, src/handlers.py
Symbols: authenticate(), UserSession, validate_token()
References: src/middleware.py:45 (calls authenticate), tests/test_auth.py:12
```

**Review criteria (identical to RepoPrompt):**

| Review | Criteria |
|--------|----------|
| Plan | Completeness, Feasibility, Clarity, Architecture, Risks, Scope, Testability |
| Impl | Correctness, Simplicity, DRY, Architecture, Edge Cases, Tests, Security |

**Receipt schema (Ralph-compatible):**

Impl review receipt:
```json
{
  "type": "impl_review",
  "id": "fn-1.3",
  "mode": "codex",
  "verdict": "SHIP",
  "session_id": "thread_abc123",
  "timestamp": "2026-01-11T10:30:00Z"
}
```

Completion review receipt:
```json
{
  "type": "completion_review",
  "id": "fn-1",
  "mode": "codex",
  "verdict": "SHIP",
  "session_id": "thread_xyz456",
  "timestamp": "2026-01-11T10:30:00Z"
}
```

**Session continuity:** Receipt includes `session_id` (thread_id from codex). Subsequent reviews read the existing receipt and resume the conversation, maintaining full context across fix → re-review cycles.

**Embedding budget (`FLOW_CODEX_EMBED_MAX_BYTES`):** Optional limit on the total bytes of file contents embedded into the review prompt (diff excluded). Default `0` (unlimited). Set to a value like `500000` (500KB) to cap prompt size.

**Sandbox mode (`--sandbox`):** Controls Codex CLI's file system access. Available modes:
- `read-only` (default on Unix) — Can only read files
- `workspace-write` — Can write files in workspace
- `danger-full-access` — Full file system access (required for Windows)
- `auto` — Resolves to `danger-full-access` on Windows, `read-only` on Unix

**Windows users:** Codex CLI's `read-only` sandbox blocks ALL shell commands on Windows (including reads). Use `--sandbox auto` or `--sandbox danger-full-access` for Windows compatibility.

**Note:** After plugin update, re-run `/nbench:setup` or `/nbench:ralph-init` to get sandbox fixes.

### checkpoint

Save and restore epic state (used during review-fix cycles).

```bash
# Save epic state to .nbench/.checkpoint-fn-1.json
nbenchctl checkpoint save --epic fn-1 [--json]

# Restore epic state from checkpoint
nbenchctl checkpoint restore --epic fn-1 [--json]

# Delete checkpoint
nbenchctl checkpoint delete --epic fn-1 [--json]
```

Checkpoints preserve full epic + task state. Useful when compaction occurs during plan-review cycles.

### status

Show `.nbench/` state summary.

```bash
nbenchctl status [--json]
```

Output:
```json
{"success": true, "epic_count": 2, "task_count": 5, "done_count": 2, "active_runs": []}
```

Human-readable output shows epic/task counts and any active Ralph runs.

### state-path

Show the resolved state directory path (useful for debugging parallel worktree setups).

```bash
nbenchctl state-path [--json]
```

Output:
```json
{"success": true, "state_dir": "/repo/.git/flow-state", "source": "git-common-dir"}
```

Source values:
- `env` — `FLOW_STATE_DIR` environment variable
- `git-common-dir` — `git --git-common-dir` (shared across worktrees)
- `fallback` — `.nbench/state` (non-git or old git)

### migrate-state

Migrate existing repos to the shared runtime state model.

```bash
nbenchctl migrate-state [--clean] [--json]
```

Options:
- `--clean` — Remove runtime fields from tracked JSON files after migration (recommended for cleaner git diffs)

What it does:
1. Scans all task JSON files for runtime fields (`status`, `assignee`, `claimed_at`, etc.)
2. Writes those fields to the state directory (`.git/flow-state/tasks/`)
3. With `--clean`: removes runtime fields from the original JSON files

**When to use:**
- After upgrading to 0.17.0+ if you want parallel worktree support
- To clean up git diffs (runtime changes no longer tracked)

**Not required** for normal operation — the merged read path handles backward compatibility automatically.

## Ralph Receipts

RepoPrompt review receipts are written by the review skills (not nbenchctl commands). Codex review receipts are written by `nbenchctl codex impl-review` and `nbenchctl codex completion-review` when `--receipt` is provided. Ralph sets `REVIEW_RECEIPT_PATH` to coordinate both.

See: [Ralph deep dive](ralph.md)

## JSON Output

All commands support `--json` (except `cat`). Wrapper format:

```json
{"success": true, ...}
{"success": false, "error": "message"}
```

Exit codes: 0=success, 1=general error, 2=tool/parse error, 3=sandbox configuration error.

## Error Handling

- Missing `.nbench/`: "Run 'nbenchctl init' first"
- Invalid ID format: "Expected format: fn-N (epic) or fn-N.M (task)"
- File conflicts: Refuses to overwrite existing epics/tasks
- Dependency violations: Same-epic only, must exist, no cycles
- Status violations: Can't start non-todo, can't close with incomplete tasks
